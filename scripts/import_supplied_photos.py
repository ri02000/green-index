#!/usr/bin/env python3
"""Apply a user-supplied, SKU-matched archive of WebP photos atomically."""
import base64
import csv
import hashlib
import io
import json
import re
import zipfile
from pathlib import Path

ROOT=Path('.')
parts=sorted((ROOT/'photo_transfer').glob('part*.txt'))
assert parts, 'No photo transfer parts'
b64=''.join(p.read_text(encoding='ascii').strip() for p in parts)
archive=base64.b64decode(b64,validate=True)
with zipfile.ZipFile(io.BytesIO(archive)) as z:
    files={n:z.read(n) for n in z.namelist() if not n.endswith('/')}
assert len(files)==33, f'Expected 33 unique files, got {len(files)}'
assert all(re.fullmatch(r'\d{8}\.webp',n) and data[:4]==b'RIFF' and data[8:12]==b'WEBP' for n,data in files.items()), 'Unexpected photo format or code'

csv_path=ROOT/'products.csv'
with csv_path.open('r',encoding='utf-8-sig',newline='') as f:
    reader=csv.DictReader(f)
    fields=reader.fieldnames
    rows=list(reader)
by_code={r['code']:r for r in rows}
assert len(by_code)==len(rows), 'Duplicate catalog codes'
image_paths={}
for n,data in files.items():
    code=n[:-5]
    assert code in by_code, f'Unknown catalog SKU {code}'
    item=by_code[code]
    assert not item['image_path'], f'Existing photo would be overwritten: {code}'
    target=ROOT/'photos'/n
    assert not target.exists(), f'Existing file would be overwritten: {n}'
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(data)
    image_paths[code]=f'photos/{n}'
    item['image_path']=image_paths[code]
    item['image_kind']='user_supplied_product_photo'

page_data=[]
for name in ('index.html','share.html'):
    page=ROOT/name
    html=page.read_text(encoding='utf-8')
    m=re.search(r'const DATA=(\[[\s\S]*?\]);',html)
    assert m, f'Missing DATA in {name}'
    data=json.loads(m.group(1))
    assert len(data)==len(rows), f'Count mismatch in {name}'
    assert [str(d['code']) for d in data]==[r['code'] for r in rows], f'SKU order mismatch in {name}'
    for product in data:
        code=str(product['code'])
        if code in image_paths:
            assert not product['image_path'], f'Page image would be overwritten {name}: {code}'
            product['image_path']=image_paths[code]
            product['image_kind']='user_supplied_product_photo'
    replacement='const DATA='+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';'
    html=html[:m.start()]+replacement+html[m.end():]
    page.write_text(html,encoding='utf-8')
    page_data.append(data)
assert page_data[0]==page_data[1], 'Main and share catalogs diverged'
assert sum(bool(r['image_path']) for r in rows)==165, 'Expected 165 photo links after import'
assert all(x['image_path']==y['image_path'] and x['image_kind']==y['image_kind'] for x,y in zip(rows,page_data[0])), 'Image path mismatch'
with csv_path.open('w',encoding='utf-8-sig',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=fields,lineterminator='\r\n')
    writer.writeheader()
    writer.writerows(rows)

report={
 'source':'user provided archive with 33 product photos',
 'registered_products':len(rows),
 'imported_photos':len(files),
 'photos_linked':sum(bool(r['image_path']) for r in rows),
 'photos_missing':sum(not r['image_path'] for r in rows),
 'items':[{'code':code,'name':by_code[code]['name'],'path':path,'sha256':hashlib.sha256(files[path.split('/')[-1]]).hexdigest()} for code,path in sorted(image_paths.items())],
}
(ROOT/'photo_import_user_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k!='items'},ensure_ascii=False))
