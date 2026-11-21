#!/usr/bin/env python3
"""Conservatively test a single likely first-party CDN photo filename per oil.

Hypothesized paths are never treated as real until the remote server returns an
actual PNG with HTTP 200. The script makes no attempt to bypass restrictions.
"""
import concurrent.futures
import csv
import json
import re
import urllib.parse
import urllib.request
import urllib.error
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOST = "prd-evo-content.doterra.com"
BASE = "https://" + HOST + "/apac/korea/images/product-imagery/essential-oil-imagery/"
UA = "GreenIndexPhotoIndexer/1.0 (candidate filename check)"


def predict(product):
    if product["category"] not in ("싱글 오일", "블렌드 오일"):
        return None
    code = product["code"]
    if not re.fullmatch(r"\d{8}", code):
        return None
    vol = re.search(r"(\d+)\s*mL", product["volume"], re.I)
    if not vol:
        return None
    parsed = urllib.parse.urlparse(product["detail_source"])
    slug = parsed.path.strip("/").split("/")[-1]
    if slug.endswith("-oil"):
        slug = slug[:-4]
    slug = slug.removeprefix("doterra-").replace("-", "_")
    if not re.fullmatch(r"[a-z0-9_]{3,80}", slug):
        return None
    cat = "single-oils-imagery" if product["category"] == "싱글 오일" else "blend-oils-imagery"
    return BASE + cat + "/" + vol.group(1) + "ml_" + slug + "_" + code + "_650tall_kr.png"


def attempt(item):
    product, url = item
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": UA, "Accept": "image/png,image/*;q=0.5",
            "Referer": "https://ri02000.github.io/green-index/"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            first = resp.read(16)
            okay = resp.status == 200 and "image/" in resp.headers.get("Content-Type", "") and first.startswith(b"\x89PNG\r\n\x1a\n")
            status = "verified_png" if okay else "not_image"
    except urllib.error.HTTPError as e:
        status = "HTTP_" + str(e.code)
    except Exception as e:
        status = type(e).__name__
    return {"product_code": product["code"], "name": product["name"], "image_url": url, "status": status}


def main():
    with (ROOT / "products.csv").open(encoding="utf-8-sig", newline="") as f:
        products = list(csv.DictReader(f))
    with (ROOT / "image_sources.csv").open(encoding="utf-8", newline="") as f:
        existing = list(csv.DictReader(f))
    known = {p["product_code"] for p in existing}
    uploaded = {p.stem for p in (ROOT / "photos").glob("*.webp")}
    candidates = [(p, predict(p)) for p in products if p["code"] not in known | uploaded]
    candidates = [(p, u) for p, u in candidates if u]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(attempt, candidates))
    hits = [r for r in results if r["status"] == "verified_png"]
    fields = ["product_code", "name", "image_url", "status"]
    with (ROOT / "image_pattern_probe.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(results)
    # Append only URLs tested as real PNG files, so future audits can reuse them.
    for r in hits:
        if r["product_code"] in known:
            continue
        existing.append({"product_code": r["product_code"], "product_label": r["name"],
                         "image_url": r["image_url"], "source": "doTERRA Korea official CDN HTTP 200 PNG",
                         "review_status": "verified_image_response_visual_label_pending"})
        known.add(r["product_code"])
    with (ROOT / "image_sources.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["product_code","product_label","image_url","source","review_status"])
        w.writeheader()
        w.writerows(existing)
    summary = {"checked_at_utc": datetime.now(timezone.utc).isoformat(),
               "attempted": len(results), "valid_official_pngs": len(hits),
               "results": dict(Counter(r["status"] for r in results)),
               "note": "Filename inference tested; a 200 PNG is not permission to republish or proof of current label."}
    (ROOT / "image_pattern_probe_report.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Official CDN filename tests:", summary, flush=True)


if __name__ == "__main__":
    main()
