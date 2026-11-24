from pathlib import Path
import json
from PIL import Image
path=Path('photos/60228342.webp')
assert path.exists(), 'Missing official source photo'
source=Image.open(path).convert('RGBA')
assert source.size==(320,520),source.size
# Remove brochure's neighboring layout fragments and the footer logo.
product=source.crop((114,20,208,464))
canvas=Image.new('RGBA',(320,520),(255,255,255,0))
height=468
width=round(product.width*height/product.height)
product=product.resize((width,height),Image.Resampling.LANCZOS)
canvas.alpha_composite(product,((320-width)//2,(520-height)//2))
canvas.save(path,'WEBP',quality=96,method=6)
report=Path('official_helichrysum_photo_import.json')
record=json.loads(report.read_text(encoding='utf-8'))
record['cropped_to_product_only']=True
record['brochure_footer_removed']=True
report.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Product-only crop prepared',path,canvas.size)
