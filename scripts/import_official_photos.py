#!/usr/bin/env python3
"""Conservative Green Index photo import. Use only reviewed, first-party URLs.

Source URLs must include the exact product code. Do not bypass access controls.
This script logs failures and does not invent substitute photos.
"""
import csv
import io
import json
import re
import time
import urllib.request
import urllib.error
import urllib.parse
import urllib.robotparser
from pathlib import Path
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
USER_AGENT = "GreenIndexCatalog/0.1 (+https://github.com/ri02000/green-index; product image verification)"
HOST = "prd-evo-content.doterra.com"

def allowed_by_robots(url):
    p = urllib.parse.urlparse(url)
    if p.hostname != HOST or p.scheme != "https":
        return False, "not approved first-party image host"
    # Fail closed on inaccessible robots.txt. A 404 means no robots restrictions.
    robots_url = "https://" + HOST + "/robots.txt"
    try:
        request = urllib.request.Request(robots_url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=15) as response:
            content = response.read(200000).decode("utf-8", errors="ignore")
    except urllib.error.HTTPError as ex:
        if ex.code == 404:
            return True, "robots.txt absent"
        return False, "robots.txt HTTP " + str(ex.code)
    except Exception as ex:
        return False, "robots.txt inaccessible: " + str(ex)[:100]
    rp = urllib.robotparser.RobotFileParser()
    rp.parse(content.splitlines())
    return rp.can_fetch(USER_AGENT, url), "robots checked"

def import_one(code, url):
    if not re.fullmatch(r"\d{8}", code) or code not in url:
        return "skip: image filename or URL lacks exact product number"
    allowed, reason = allowed_by_robots(url)
    if not allowed:
        return "skip: " + reason
    dest = ROOT / "photos" / (code + ".webp")
    if dest.exists():
        return "exists: " + dest.relative_to(ROOT).as_posix()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=30) as resp:
            if resp.status != 200:
                return "HTTP " + str(resp.status)
            data = resp.read(5_000_001)
        if len(data) > 5_000_000:
            return "skip: file larger than limit"
        image = ImageOps.exif_transpose(Image.open(io.BytesIO(data)))
        image.verify()
        image = ImageOps.exif_transpose(Image.open(io.BytesIO(data))).convert("RGB")
        if image.width < 100 or image.height < 100:
            return "skip: image too small"
        image.thumbnail((600, 750), Image.Resampling.LANCZOS)
        dest.parent.mkdir(parents=True, exist_ok=True)
        image.save(dest, "WEBP", quality=82, method=6)
        return "downloaded: " + dest.relative_to(ROOT).as_posix()
    except Exception as ex:
        return "failed: " + str(ex)[:200]

def main():
    with open(ROOT / "products.csv", encoding="utf-8-sig", newline="") as f:
        product_rows = list(csv.DictReader(f))
    code_set = {p["code"] for p in product_rows}
    results = []
    with open(ROOT / "image_sources.csv", encoding="utf-8", newline="") as f:
        sources = list(csv.DictReader(f))
    for source in sources:
        code, url = source["product_code"], source["image_url"]
        status = import_one(code, url) if code in code_set else "skip: product not in DB"
        results.append({"code": code, "image_url": url, "status": status})
        print(code, status)
        time.sleep(1.5)
    # Only assign photo paths when the actual local files exist.
    for p in product_rows:
        local = ROOT / "photos" / (p["code"] + ".webp")
        if local.is_file():
            p["image_path"] = "photos/" + p["code"] + ".webp"
            p["image_kind"] = "official_candidate_image"
    with open(ROOT / "products.csv", encoding="utf-8", newline="w") as f:
        writer = csv.DictWriter(f, fieldnames=list(product_rows[0].keys()))
        writer.writeheader()
        writer.writerows(product_rows)
    # Preserve all the existing detailed HTML data and only adjust image fields.
    for file in ["index.html", "share.html"]:
        path = ROOT / file
        source = path.read_text("utf-8")
        match = re.search(r"const DATA=(\[.*?\]);\s*const byCode", source, re.S)
        if not match:
            raise SystemExit("Missing embedded product database in " + file)
        data = json.loads(match.group(1))
        for p in data:
            local = ROOT / "photos" / (p["code"] + ".webp")
            if local.is_file():
                p["image_path"] = "photos/" + p["code"] + ".webp"
                p["image_kind"] = "official_candidate_image"
        source = source[:match.start(1)] + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + source[match.end(1):]
        path.write_text(source, "utf-8")
    (ROOT / "image_import_report.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Images available locally:", len(list((ROOT / "photos").glob("*.webp"))))
    print("Warning: photographs require separate publishing-rights review.")

if __name__ == "__main__":
    main()
