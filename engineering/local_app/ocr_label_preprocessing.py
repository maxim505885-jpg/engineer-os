"""Explicit, fixed label transforms; no text correction or source modification."""
import io,math
from PIL import Image,ImageOps

MAX_PIXELS=9000000
MAX_PNG_BYTES=2*1024*1024

def prepare(png,profile,*,version=2):
    if type(version)!=int or version not in (1,2):raise ValueError('OCR_INVALID_TRANSFORM_VERSION')
    if profile not in ('padded','italic'):raise ValueError('OCR_INVALID_PREPROCESSING')
    with Image.open(io.BytesIO(png)) as source:
        w,h=source.size
        shear=.1 if profile=='italic' else 0
        width=w+math.floor(h*shear)+1 if shear else w
        pad=20
        if (width+2*pad)*(h+2*pad)>MAX_PIXELS:raise ValueError('OCR_PIXEL_LIMIT')
        image=source.convert('RGB')
    if shear:
        # Keep dark neutral ink, remove saturated drawing background. Signs and
        # punctuation are preserved without component-size or word filters.
        # v2 excludes medium-gray antialiasing that joined the small italic
        # Cyrillic strokes in the pinned real-label corpus. Retain v1 for
        # verification of historical derivative receipts, never autocorrect text.
        ink=bytearray(w*h)
        for i,(r,g,b) in enumerate(image.getdata()):
            gray=round(.299*r+.587*g+.114*b)
            ink[i]=0 if gray<(100 if version==1 else 80) and max(r,g,b)-min(r,g,b)<70 else 255
        image=Image.frombytes('L',(w,h),bytes(ink))
        image=image.transform((width,h),Image.Transform.AFFINE,(1,-shear,0,0,1,0),resample=Image.Resampling.BILINEAR,fillcolor=255)
    image=ImageOps.expand(image,pad,'white')
    output=io.BytesIO();image.save(output,format='PNG');raw=output.getvalue()
    if len(raw)>MAX_PNG_BYTES:raise ValueError('OCR_OUTPUT_LIMIT')
    return raw,dict(profile=profile,width=image.width,height=image.height,shear=shear,padding=pad,
        purpose='DERIVED_OCR_INPUT_UNVERIFIED',source_equivalence='NOT_ASSERTED',transform_version=version)
