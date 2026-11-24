from pathlib import Path
import io,json,requests,fitz
from PIL import Image
URL='https://media.doterra.com/kr/ko/flyers/2025_convention_brochure.pdf'
r=requests.get(URL,timeout=55);r.raise_for_status()
doc=fitz.open(stream=r.content,filetype='pdf')
page=doc[4]
entries=[x for x in page.get_images(full=True) if x[0]==284 and x[1]==2462]
assert len(entries)==1,'Expected official product photograph unavailable'
base=fitz.Pixmap(doc,284)
mask=fitz.Pixmap(doc,2462)
assert base.width==mask.width and base.height==mask.height
if base.n not in (3,4):base=fitz.Pixmap(fitz.csRGB,base)
rgba=fitz.Pixmap(base,mask)
assert rgba.n==4
img=Image.frombytes('RGBA',(rgba.width,rgba.height),rgba.samples)
bbox=img.getchannel('A').getbbox()
assert bbox and bbox[2]-bbox[0]>40 and bbox[3]-bbox[1]>120,('Invalid alpha bounds',bbox)
cut=img.crop(bbox)
scale=min(470/cut.height,268/cut.width)
size=(max(1,round(cut.width*scale)),max(1,round(cut.height*scale)))
cut=cut.resize(size,Image.Resampling.LANCZOS)
canvas=Image.new('RGBA',(320,520),(255,255,255,0))
canvas.alpha_composite(cut,((320-size[0])//2,(520-size[1])//2))
out=Path('photos/60228342.webp')
assert out.exists()
canvas.save(out,'WEBP',quality=95,method=6)
report=Path('official_helichrysum_photo_import.json')
d=json.loads(report.read_text(encoding='utf-8'))
d['embedded_source_image_xref']=284
d['embedded_alpha_xref']=2462
d['precise_extraction']=True
d['source_pixels']=[img.width,img.height]
d['alpha_bounds']=list(bbox)
report.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print({'processed':str(out),'size':canvas.size,'source':img.size,'bbox':bbox})
