#!/usr/bin/env python3
"""Check whether cataloged first-party product pictures are actual image files.

Never bypass blocks or change publicly displayed product photos. Only use
candidate URLs already discovered from official source pages.
"""
import csv
import io
import json
import re
import urllib.error
import urllib.parse
import urllib.request
import concurrent.futures
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
UA = "GreenIndexPhotoIndexer/1.0 (image link verification)"
MAX_READ = 4096


def priority(row):
    url = row["url"]
    return (int("prd-evo-content.doterra.com" in url),
            int("2x3" in url or "566x819" in url or "600x900" in url),
            int(row["origin"].startswith("img:src")),
            int("og:image" not in row["origin"]),
            int("650tall" in url),
            -len(url))


def probe(row):
    result = dict(row)
    url = row["url"]
    p = urllib.parse.urlparse(url)
    if p.scheme != "https" or p.hostname not in {"www.doterra.com", "prd-evo-content.doterra.com"}:
        result["result"] = "unapproved_host"
        return result
    try:
        request = urllib.request.Request(url, headers={
            "User-Agent": UA,
            "Accept": "image/avif,image/webp,image/png,image/jpeg,*/*;q=0.8",
            "Referer": "https://ri02000.github.io/green-index/"
        })
        with urllib.request.urlopen(request, timeout=12) as resp:
            media = resp.headers.get("Content-Type", "").split(";")[0].lower()
            result["status"] = str(resp.status)
            result["content_type"] = media
            result["size_header"] = resp.headers.get("Content-Length", "")
            payload = resp.read(MAX_READ)
            plausible = (payload[:3] == b"\xff\xd8\xff" or
                         payload[:8] == b"\x89PNG\r\n\x1a\n" or
                         payload[:4] == b"RIFF" or
                         payload[:4] == b"\x00\x00\x00\x1c")
            result["result"] = "readable_image" if resp.status == 200 and media.startswith("image/") and plausible else "not_an_image"
    except urllib.error.HTTPError as e:
        result["result"] = "HTTP_" + str(e.code)
        result["status"] = str(e.code)
    except Exception as e:
        result["result"] = type(e).__name__
    return result


def main():
    with (ROOT / "image_candidates.csv").open(encoding="utf-8-sig", newline="") as f:
        candidates = list(csv.DictReader(f))
    with (ROOT / "products.csv").open(encoding="utf-8-sig", newline="") as f:
        products = list(csv.DictReader(f))
    already = {p.stem for p in (ROOT / "photos").glob("*.webp")}
    available = {}
    for row in candidates:
        code = row["product_code"]
        if code in already:
            continue
        if not re.search(r"(?<!\d)" + re.escape(code) + r"(?!\d)", row["url"]):
            continue
        available.setdefault(code, []).append(row)
    # Try up to four distinct official URLs for each product so a failed
    # preferred CDN path does not hide a working official product photo.
    trials = []
    for code, rows in available.items():
        seen = set()
        for row in sorted(rows, key=priority, reverse=True):
            if row["url"] not in seen and len(seen) < 4:
                trials.append(row)
                seen.add(row["url"])
    print("Probe official candidate URLs:", len(trials),
          "across products:", len(available), flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        all_results = list(pool.map(probe, trials))
    # Exactly one chosen probe per product, with a successful image preferred.
    by_code = {}
    for row in all_results:
        code = row["product_code"]
        if code not in by_code or (
            row["result"] == "readable_image" and
            by_code[code]["result"] != "readable_image"
        ):
            by_code[code] = row
    results = sorted(by_code.values(), key=lambda x: x["product_code"])
    fields = ["product_code", "name", "url", "confidence", "origin", "source_page", "publication", "result", "status", "content_type", "size_header"]
    with (ROOT / "official_image_probe.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(results)
    report = {"checked_at_utc": datetime.now(timezone.utc).isoformat(),
              "database_products": len(products), "user_uploaded_photos": len(already),
              "official_photo_products_probed": len(results),
              "readable_official_images": sum(x.get("result") == "readable_image" for x in results),
              "results": dict(Counter(x["result"] for x in results)),
              "note": "Readability does not imply rights to republish or confirm packaging currency."}
    (ROOT / "official_image_probe_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Image response status:", report["results"], flush=True)


if __name__ == "__main__":
    main()
