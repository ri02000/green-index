#!/usr/bin/env python3
"""Build a source-backed image URL inventory for Green Index.

Only first-party doTERRA hosts are considered. No access-control bypass, no
photo publication, and no guesses about product-code-to-photo matches.
"""
import concurrent.futures
import csv
import html
import json
import re
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from collections import Counter
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UA = "GreenIndexPhotoIndexer/1.0 (catalog source audit)"
HEADERS = {"User-Agent": UA, "Accept": "text/html,application/xhtml+xml,image/avif,image/webp,image/png,*/*;q=0.5"}
ALLOWED = {"shop.doterra.com", "www.doterra.com", "wave0.doterra.com", "prd-evo-content.doterra.com"}
IMAGE_URL = re.compile(r"https?://[^\s\"'<>\\]+?\.(?:png|jpg|jpeg|webp)(?:\?[^\s\"'<>\\]*)?", re.I)
CODES = re.compile(r"(?<!\d)\d{8}(?!\d)")
MAX_PAGE = 1_500_000


def get_url(url, nbytes=MAX_PAGE):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=9) as res:
        final = urllib.parse.urlparse(res.url)
        if final.hostname not in ALLOWED or final.scheme != "https":
            raise ValueError("redirected outside approved doTERRA site")
        return res.read(nbytes).decode("utf-8", "replace"), int(res.status), res.url


def robots_ok(host):
    url = "https://" + host + "/robots.txt"
    try:
        body, status, final = get_url(url, 250000)
    except urllib.error.HTTPError as e:
        return False, "robots HTTP " + str(e.code)
    except Exception as e:
        return False, "robots unavailable: " + type(e).__name__
    if status != 200:
        return False, "robots status " + str(status)
    parser = urllib.robotparser.RobotFileParser()
    parser.parse(body.splitlines())
    return parser.can_fetch(UA, "https://" + host + "/KR/ko_KR/"), "robots checked"


class AssetParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.assets = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "img":
            for key in ("src", "data-src", "data-original", "data-lazy-src", "srcset"):
                if a.get(key):
                    self.assets.append((a[key], "img:" + key, a.get("alt", "")))
        elif tag == "meta" and a.get("property", "").lower() in ("og:image", "og:image:url"):
            self.assets.append((a.get("content", ""), "og:image", ""))
        elif tag == "source":
            if a.get("srcset"):
                self.assets.append((a["srcset"], "source:srcset", ""))


def normalize_asset(candidate, base):
    candidate = html.unescape(candidate).replace(r"\/", "/").replace(r"\u002F", "/")
    candidate = candidate.strip().split()[0].strip(",")
    try:
        url = urllib.parse.urljoin(base, candidate)
        p = urllib.parse.urlparse(url)
        if p.scheme != "https" or p.hostname not in ALLOWED or not re.search(r"\.(?:png|jpg|jpeg|webp)$", p.path, re.I):
            return ""
        return urllib.parse.urlunparse((p.scheme, p.netloc, p.path, "", p.query, ""))
    except Exception:
        return ""


def fetch_one(row, robots):
    code = row["code"].strip()
    name = row["name"].strip()
    page = row.get("detail_source", "").strip()
    if not page or not page.startswith("https://"):
        return {"code": code, "name": name, "result": "no_product_page", "candidates": []}
    host = urllib.parse.urlparse(page).hostname
    if host not in ALLOWED:
        return {"code": code, "name": name, "result": "not_first_party", "candidates": []}
    if not robots.get(host, (False, ""))[0]:
        return {"code": code, "name": name, "result": "robots_unavailable_or_disallowed", "candidates": []}
    try:
        content, status, final = get_url(page)
        if "maintenance.doterra.com" in content[:2000].lower():
            return {"code": code, "name": name, "result": "maintenance_page", "candidates": []}
        parser = AssetParser()
        parser.feed(content)
        candidates = {}
        for raw, source, alt in parser.assets:
            u = normalize_asset(raw, final)
            if u:
                candidates[u] = {"url": u, "discovery": source, "alt": alt[:100]}
        text = html.unescape(content).replace(r"\/", "/").replace(r"\u002F", "/")
        for m in IMAGE_URL.finditer(text):
            u = normalize_asset(m.group(0), final)
            if u and u not in candidates:
                candidates[u] = {"url": u, "discovery": "html-embedded", "alt": ""}
        out = []
        for c in candidates.values():
            if CODES.search(c["url"]) and not re.search(r"(?<!\d)" + re.escape(code) + r"(?!\d)", c["url"]):
                continue  # Different product code, never present as a candidate.
            exact = bool(re.search(r"(?<!\d)" + re.escape(code) + r"(?!\d)", c["url"]))
            if exact or (name.lower() in c["alt"].lower() and len(name) > 3):
                c["confidence"] = "code_in_image_url" if exact else "name_in_image_alt_needs_review"
                out.append(c)
        return {"code": code, "name": name, "result": "discovered" if out else "no_code_matching_image", "candidates": out[:10], "source_page": final}
    except urllib.error.HTTPError as e:
        return {"code": code, "name": name, "result": "HTTP_" + str(e.code), "candidates": []}
    except Exception as e:
        return {"code": code, "name": name, "result": "error_" + type(e).__name__, "candidates": []}



def collect_category_page(url):
    """Read a public, robots-allowed catalog category and collect code-bearing assets."""
    try:
        body, _, final = get_url(url)
        if "maintenance.doterra.com" in body[:2000].lower():
            return {"page": url, "result": "maintenance", "assets": [], "category_links": []}
        parser = AssetParser()
        parser.feed(body)
        text = html.unescape(body).replace(r"\/", "/").replace(r"\u002F", "/")
        raw = [(x, origin) for x, origin, _ in parser.assets]
        raw.extend((m.group(0), "html-embedded") for m in IMAGE_URL.finditer(text))
        found = {}
        for asset, origin in raw:
            u = normalize_asset(asset, final)
            if not u or not CODES.search(u):
                continue
            found[u] = {"url": u, "discovery": "category:" + origin, "page": final}
        links = []
        for h in re.findall(r'<a\s[^>]*href\s*=\s*["\x27]([^"\x27]+)["\x27]', body, re.I):
            u = urllib.parse.urljoin(final, html.unescape(h))
            p = urllib.parse.urlparse(u)
            if p.hostname == "www.doterra.com" and p.path.startswith("/KR/ko_KR/pl/"):
                links.append(urllib.parse.urlunparse((p.scheme, p.netloc, p.path, "", "", "")))
        return {"page": final, "result": "ok", "assets": list(found.values()), "category_links": sorted(set(links))}
    except urllib.error.HTTPError as e:
        return {"page": url, "result": "HTTP_" + str(e.code), "assets": [], "category_links": []}
    except Exception as e:
        return {"page": url, "result": type(e).__name__, "assets": [], "category_links": []}


def main():
    with (ROOT / "products.csv").open(encoding="utf-8-sig", newline="") as f:
        products = list(csv.DictReader(f))
    with (ROOT / "image_sources.csv").open(encoding="utf-8", newline="") as f:
        seeds = list(csv.DictReader(f))
    product_codes = {p["code"] for p in products}
    hosts = {urllib.parse.urlparse(p["detail_source"]).hostname for p in products if p.get("detail_source")}
    robots = {host: robots_ok(host) for host in sorted(hosts & ALLOWED)}
    print("Robots access results:", robots, flush=True)

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        scanned = list(pool.map(lambda p: fetch_one(p, robots), products))
    records = {}
    for seed in seeds:
        code = seed["product_code"]
        url = normalize_asset(seed["image_url"], seed["image_url"])
        if code in product_codes and url and re.search(r"(?<!\d)" + re.escape(code) + r"(?!\d)", url):
            records[(code, url)] = {"product_code": code, "name": seed["product_label"], "url": url,
                                     "confidence": "code_in_image_url", "origin": "existing_official_candidate",
                                     "source_page": seed["source"], "publication": "not_cleared"}
    for scan in scanned:
        for c in scan["candidates"]:
            key = (scan["code"], c["url"])
            records[key] = {"product_code": scan["code"], "name": scan["name"], "url": c["url"],
                            "confidence": c["confidence"], "origin": c["discovery"],
                            "source_page": scan.get("source_page", ""), "publication": "not_cleared"}
    category_scans = []
    if robots.get("www.doterra.com", (False, ""))[0]:
        homepage = collect_category_page("https://www.doterra.com/KR/ko_KR/shop-home")
        category_scans.append(homepage)
        pages = sorted(set(homepage["category_links"] + [
            "https://www.doterra.com/KR/ko_KR/pl/single-oils",
            "https://www.doterra.com/KR/ko_KR/pl/blend-oils"
        ]))[:70]
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            category_scans.extend(pool.map(collect_category_page, pages))
        for listing in category_scans:
            for candidate in listing["assets"]:
                codes = CODES.findall(candidate["url"])
                for code in set(codes) & product_codes:
                    key = (code, candidate["url"])
                    if key not in records:
                        product = next(p for p in products if p["code"] == code)
                        records[key] = {"product_code": code, "name": product["name"], "url": candidate["url"],
                                        "confidence": "code_in_image_url", "origin": candidate["discovery"],
                                        "source_page": listing["page"], "publication": "not_cleared"}
    rows = sorted(records.values(), key=lambda r: (r["product_code"], r["url"]))
    fields = ["product_code", "name", "url", "confidence", "origin", "source_page", "publication"]
    with (ROOT / "image_candidates.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    local = {p.stem for p in (ROOT / "photos").glob("*.webp")}
    report = {"checked_at_utc": datetime.now(timezone.utc).isoformat(),
              "total_database_products": len(products),
              "local_user_supplied_photo_count": len(local & product_codes),
              "photos_missing_locally": len(product_codes - local),
              "first_party_image_url_candidates": len(rows),
              "products_with_official_image_url_candidates": len({r["product_code"] for r in rows}),
              "robots": {k: {"allowed": v[0], "reason": v[1]} for k, v in robots.items()},
              "discovery_result_counts": dict(Counter(r["result"] for r in scanned)),
              "category_page_scan_count": len(category_scans),
              "category_page_results": dict(Counter(s["result"] for s in category_scans)),
              "scans": scanned}
    (ROOT / "image_crawl_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Image candidate URLs:", len(rows), flush=True)
    print("Product scans:", report["discovery_result_counts"], flush=True)
    print("Images are research candidates only, not permission to republish.", flush=True)


if __name__ == "__main__":
    main()
