#!/usr/bin/env python3
"""Per-product missing-photo audit; never infer a photo from a failed URL."""
import csv, json
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
ROOT=Path(__file__).resolve().parents[1]
def read(name):
    with (ROOT/name).open(encoding="utf-8-sig",newline="") as f:
        return list(csv.DictReader(f))
def main():
    products=read("products.csv")
    probes=read("official_image_probe.csv")
    candidates=read("image_candidates.csv")
    by_probe={p["product_code"]:p for p in probes}
    by_candidate={}
    for p in candidates:
        by_candidate.setdefault(p["product_code"],[]).append(p)
    rows=[]
    for p in products:
        if p.get("image_path"):
            continue
        code=p["code"]
        trial=by_probe.get(code)
        options=by_candidate.get(code,[])
        if trial and trial["result"]=="readable_image":
            reason="verified_but_not_linked_review_required"
        elif trial and trial["result"].startswith("HTTP_"):
            reason="candidate_unavailable_"+trial["result"]
        elif trial:
            reason="candidate_failed_"+trial["result"]
        elif options:
            reason="candidate_not_probed"
        else:
            reason="no_code_matching_official_image"
        rows.append({"product_code":code,"name":p["name"],"category":p["category"],
            "reason":reason,"official_product_page":p.get("detail_source",""),
            "candidate_count":str(len(options)),
            "last_tested_url":trial["url"] if trial else "",
            "last_test_result":trial["result"] if trial else "",
            "next_action":"review_official_product_page_or_current_label",
            "checked_at_utc":datetime.now(timezone.utc).isoformat()})
    fields=["product_code","name","category","reason","official_product_page",
        "candidate_count","last_tested_url","last_test_result","next_action","checked_at_utc"]
    with (ROOT/"missing_photo_audit.csv").open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    summary={"checked_at_utc":datetime.now(timezone.utc).isoformat(),
        "total_products":len(products),
        "photo_linked":len(products)-len(rows),
        "photos_missing":len(rows),
        "reasons":dict(Counter(p["reason"] for p in rows)),
        "note":"An HTTP 404 or absent image is not permission to guess a filename. Publication rights and packaging currency have not been verified."}
    (ROOT/"missing_photo_audit_report.json").write_text(
        json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,ensure_ascii=False))
if __name__=="__main__":
    main()
