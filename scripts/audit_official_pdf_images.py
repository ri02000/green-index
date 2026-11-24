import json,requests,fitz
from pathlib import Path
URL='https://media.doterra.com/kr/ko/flyers/2025_convention_brochure.pdf'
r=requests.get(URL,timeout=55);r.raise_for_status()
doc=fitz.open(stream=r.content,filetype='pdf')
p=doc[4]
result=[]
for rec in p.get_images(full=True):
    xref,smask,width,height,colorspace,bpc,*_=rec
    rects=p.get_image_rects(xref)
    for rect in rects:
        result.append({'xref':xref,'smask':smask,'pixel_width':width,'pixel_height':height,'rel_rect':[round(rect.x0/p.rect.width,4),round(rect.y0/p.rect.height,4),round(rect.x1/p.rect.width,4),round(rect.y1/p.rect.height,4)]})
Path('official_pdf_images_audit.json').write_text(json.dumps({'page':5,'images':result},indent=2)+'\n')
print(result)
