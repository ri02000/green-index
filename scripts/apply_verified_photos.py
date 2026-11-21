#!/usr/bin/env python3
"""Apply verified Korean official product photo links to the website and catalog.

Only existing products, exact product-code image URLs, verified HTTP image probes.
Never replace user images or existing working assignments. Writes both HTML pages
and CSV consistently. Outputs an audit. No external requests in this script.
"""
import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
VALID_HOSTS=("https://prd-evo-content.doterra.com/","https://www.doterra.com/")
DATA_RE=re.compile(r"(?<=const DATA=)\[[\s\S]*?\](?=;\s*const byCode=)")
FIELDS=("image_kind","image_path")

def read_csv(name):
    with (ROOT/name).open(encoding="utf-8-sig",newline="") as f:
        return list(csv.DictReader(f))

def write_csv(name,rows,fields):
    with (ROOT/name).open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

def confirmed(row):
    code=row["product_code"].strip()
    url=row["url"].strip()
    return (row.get("result")=="readable_image"
        and row.get("status")=="200"
        and row.get("content_type","").startswith("image/")
        and row.get("confidence")=="code_in_image_url"
        and url.startswith(VALID_HOSTS)
        and bool(re.search(r"(?<!\d)"+re.escape(code)+r"(?!\d)",url)))

def main():
    products=read_csv("products.csv")
    probes=read_csv("official_image_probe.csv")
    existing={p["code"] for p in products}
    by_code={p["code"]:p for p in products}
    if len(existing)!=len(products):
        raise ValueError("Duplicate product codes detected; stop rather than publish.")
    before=sum(bool(p.get("image_path")) for p in products)
    additions={}
    for p in probes:
        code=p["product_code"]
        if code not in existing or code in additions or not confirmed(p):
            continue
        if by_code[code].get("image_path"):
            continue
        additions[code]=p["url"]
    if not additions:
        print("No newly verified unassigned pictures; catalog unchanged.")
    else:
        for p in products:
            if p["code"] in additions:
                p["image_kind"]="official_first_party_external"
                p["image_path"]=additions[p["code"]]
        # Important: do not edit only one HTML page. Validate all before writing.
        staged=[]
        for page in ("index.html","share.html"):
            path=ROOT/page
            source=path.read_text(encoding="utf-8")
            found=DATA_RE.search(source)
            if not found:
                raise ValueError(f"{page}: embedded product data not found")
            items=json.loads(found.group(0))
            if len(items)!=len(products) or set(x["code"] for x in items)!=existing:
                raise ValueError(f"{page}: HTML and CSV catalog differ; stop")
            for item in items:
                if item["code"] in additions and not item.get("image_path"):
                    item["image_kind"]="official_first_party_external"
                    item["image_path"]=additions[item["code"]]
            replacement=json.dumps(items,ensure_ascii=False,separators=(",",":"))
            updated=source[:found.start()]+replacement+source[found.end():]
            json.loads(DATA_RE.search(updated).group(0))
            staged.append((path,updated))
        write_csv("products.csv",products,list(products[0]))
        for path,updated in staged:
            path.write_text(updated,encoding="utf-8")
    after=sum(bool(p.get("image_path")) for p in products)
    audit={"checked_at_utc":datetime.now(timezone.utc).isoformat(),
           "registered_products":len(products),
           "photo_links_before":before,"photo_links_after":after,
           "photos_missing":len(products)-after,
           "new_links":[{"code":k,"url":v} for k,v in sorted(additions.items())],
           "policy":"Only verified first-party Korea product-number image links; external display rights and current packaging require separate review."}
    (ROOT/"photo_import_status.json").write_text(json.dumps(audit,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in audit.items() if k!="new_links"},ensure_ascii=False))
if __name__=="__main__":
    main()
