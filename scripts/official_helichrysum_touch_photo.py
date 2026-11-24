#!/usr/bin/env python3
import csv,io,json,re
from pathlib import Path
import requests,fitz,numpy as np
from PIL import Image
code='60228342'
source_url='https://media.doterra.com/kr/ko/flyers/2025_convention_brochure.pdf'
r=requests.get(source_url,timeout=55,headers={'User-Agent':'Mozilla/5.0'})
r.raise_for_status()
assert r.content.startswith(b'%PDF')
page=fitz.open(stream=r.content,filetype='pdf')[4]
assert code in page.get_text(),'Official brochure page does not contain SKU'
box=page.rect
clip=fitz.Rect(box.width*.865,box.height*.295,box.width*.930,box.height*.725)
pix=page.get_pixmap(matrix=fitz.Matrix(4,4),clip=clip,alpha=False)
src=Image.frombytes('RGB',(pix.width,pix.height),pix.samples)
arr=np.asarray(src,dtype=np.float32)
y,x=np.where(arr.mean(axis=2)<217)
assert len(x)>400,'No bottle silhouette'
x0=max(0,int(np.percentile(x,.35))-4);x1=min(src.width,int(np.percentile(x,99.65))+5)
y0=max(0,int(np.percentile(y,.35))-4);y1=min(src.height,int(np.percentile(y,99.65))+5)
assert x1-x0>25 and y1-y0>120,'Unexpected bottle bounds'
part=arr[y0:y1,x0:x1]
alpha=np.clip((255-part.mean(axis=2)-14)/35,0,1)
rgba=np.concatenate([part.astype('uint8'),(alpha*255).astype('uint8')[:,:,None]],axis=2)
bottle=Image.fromarray(rgba,'RGBA')
canvas=Image.new('RGBA',(320,520),(255,255,255,0))
ratio=min(468/bottle.height,260/bottle.width)
size=(max(1,round(bottle.width*ratio)),max(1,round(bottle.height*ratio)))
bottle=bottle.resize(size,Image.Resampling.LANCZOS)
canvas.alpha_composite(bottle,((320-size[0])//2,(520-size[1])//2))
photo=Path('photos')/(code+'.webp')
assert not photo.exists(),'Photo exists already'
canvas.save(photo,'WEBP',quality=95,method=6)
with open('products.csv',encoding='utf-8-sig',newline='') as f:
    reader=csv.DictReader(f);columns=reader.fieldnames;rows=list(reader)
target=[r for r in rows if r['code']==code]
assert len(rows)==166 and len(target)==1 and not target[0]['image_path']
target[0]['image_kind']='official_brochure_local'
target[0]['image_path']=str(photo)
with open('products.csv','w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=columns,lineterminator='\r\n');w.writeheader();w.writerows(rows)
count_source="const photoOfficial=DATA.filter(p=>p.image_kind==='official_first_party_external'&&p.image_path).length;"
for page_name in ('index.html','share.html'):
    p=Path(page_name);html=p.read_text(encoding='utf-8')
    m=re.search(r'const DATA=(\[[\s\S]*?\]);',html)
    assert m,'Missing DATA'
    data=json.loads(m.group(1))
    row=[x for x in data if str(x['code'])==code]
    assert len(data)==166 and len(row)==1 and not row[0]['image_path']
    row[0]['image_path']=str(photo);row[0]['image_kind']='official_brochure_local'
    html=html[:m.start()]+'const DATA='+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';'+html[m.end():]
    assert count_source in html and 'photoLocal+photoOfficial}개' in html
    html=html.replace(count_source,count_source+"\nconst photoBrochure=DATA.filter(p=>p.image_kind==='official_brochure_local'&&p.image_path).length;")
    html=html.replace('photoLocal+photoOfficial}개','photoLocal+photoOfficial+photoBrochure}개',1)
    html=html.replace(' · 미확보',' / 공식 자료 1개 · 미확보',1)
    p.write_text(html,encoding='utf-8')
readme=Path('README.md');text=readme.read_text(encoding='utf-8')
text=text.replace('사진 표시 대상: 165개 제품. 1개 제품(헬리크리섬 터치 60228342)은 아직 사진이 없음.','사진 표시 대상: 166개 제품. 사진 미확보 0개.')
text+='\n## 2026-11-24 헬리크리섬 터치 사진 출처\n- 한국 도테라 공식 브로슈어 5쪽에서 제품번호 60228342와 함께 소개된 사진을 추출. 마지막 사용자 첨부 원본과 동일한 파일이라고 주장하지 않음.\n- 출처: '+source_url+'\n- 현재 166개 사진 연결, 미확보 0개. 사진 재게시 권한과 최신 포장 일치 여부는 별도 확인 대상.\n'
readme.write_text(text,encoding='utf-8')
report={'code':code,'source':source_url,'page':5,'image_path':str(photo),'image_kind':'official_brochure_local','user_uploaded_original':False,'photos_linked':sum(bool(r['image_path']) for r in rows)}
assert report['photos_linked']==166
Path('official_helichrysum_photo_import.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(report)
