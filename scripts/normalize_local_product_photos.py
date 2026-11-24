#!/usr/bin/env python3
"""Generate centered card thumbnails for local oil bottles; do not change original photos."""
import csv,json
from pathlib import Path
import numpy as np
from PIL import Image
cats={'싱글 오일','블렌드 오일','방향용 오일','터치 · 롤온','터치 · 롤온 · 스프레이'}
with open('products.csv',encoding='utf-8-sig',newline='') as f: rows=list(csv.DictReader(f))
outdir=Path('thumbs');outdir.mkdir(exist_ok=True)
result=[]
for p in rows:
    source=Path(p['image_path'])
    if not str(source).startswith('photos/') or p['category'] not in cats: continue
    if not source.is_file():raise RuntimeError('Missing original '+str(source))
    original=Image.open(source).convert('RGB');raw=np.asarray(original,dtype=np.float32);h,w=raw.shape[:2]
    hh=max(3,h//25);ww=max(3,w//25)
    border=np.concatenate([raw[:hh].reshape(-1,3),raw[-hh:].reshape(-1,3),raw[:,:ww].reshape(-1,3),raw[:,-ww:].reshape(-1,3)])
    bg=np.median(border,axis=0)
    diff=np.sqrt(np.square(raw-bg).sum(axis=2));dark=255-raw.mean(axis=2)
    alpha=np.clip((np.maximum(diff,dark*.83)-22)/40,0,1)
    mask=alpha>.38
    xx=np.where(mask.sum(axis=0)>max(2,int(h*.018)))[0]
    yy=np.where(mask.sum(axis=1)>max(2,int(w*.018)))[0]
    if not len(xx) or not len(yy):raise RuntimeError('No product foreground '+str(source))
    pad=max(1,int(min(w,h)*.012))
    x0=max(0,int(xx[0])-pad);x1=min(w,int(xx[-1])+1+pad)
    y0=max(0,int(yy[0])-pad);y1=min(h,int(yy[-1])+1+pad)
    if (x1-x0)<10 or (y1-y0)<20:raise RuntimeError('Unexpected bounds '+str(source))
    rgba=np.asarray(original.convert('RGBA')).copy()
    rgba[:,:,3]=(alpha*255).astype('uint8')
    crop=Image.fromarray(rgba).crop((x0,y0,x1,y1))
    zoom=min(350/crop.height,310/crop.width)
    dimensions=(max(1,round(crop.width*zoom)),max(1,round(crop.height*zoom)))
    crop=crop.resize(dimensions,Image.Resampling.LANCZOS)
    thumb=Image.new('RGBA',(440,440),(255,255,255,0))
    thumb.alpha_composite(crop,((440-dimensions[0])//2,(440-dimensions[1])//2))
    target=outdir/source.name
    thumb.save(target,format='WEBP',quality=93,method=6)
    result.append({'code':p['code'],'name':p['name'],'original':str(source),'thumbnail':str(target)})
if len(result)<35:raise RuntimeError('Only '+str(len(result))+' thumbnail candidates; expected >=35')
Path('photo_thumbnail_report.json').write_text(json.dumps({'created':len(result),'originals_preserved':True,'items':result},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Generated',len(result),'thumbnails')
