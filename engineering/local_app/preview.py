"""Bounded PNG view; outlines are drawn only in an in-memory PDF copy."""
import hashlib
import math
from pathlib import Path


def render_office_image(store,session_id,source_job,logical_unit,image,*,bitmap=None):
    """Decode only a revalidated referenced raster; never apply Word transforms."""
    import io
    from PIL import Image
    from .office import Package,MAX_IMAGE_BYTES
    from .source_binding import office_image_location
    child=store.extraction_job(session_id,source_job)
    if len(child['file_ids'])!=1:raise ValueError('Single Office source required')
    file=store.get_file(child['file_ids'][0])
    if Path(file['name']).suffix.lower()!='.docx':raise ValueError('Native DOCX image preview required')
    if type(image) is not int or image<1:raise ValueError('Image ordinal required')
    binding=office_image_location(store,session_id,file,source_job,logical_unit)
    images=binding['locator'].get('images',[])
    if image>len(images):raise ValueError('Image outside source element')
    descriptor=images[image-1]
    if descriptor['status']!='BOUND_PACKAGE_IMAGE':raise ValueError('Image bytes unavailable')
    with Path(file['path']).open('rb') as stream:data=stream.read(256*1024*1024+1)
    if len(data)!=file['size'] or hashlib.sha256(data).hexdigest()!=file['sha256']:raise ValueError('Office original identity changed')
    package=Package(data)
    try:
        info=package.zip.getinfo(descriptor['part'])
        if info.file_size>MAX_IMAGE_BYTES:raise ValueError('Image byte limit')
        asset=package.zip.read(descriptor['part'])
    finally:package.close()
    if len(asset)!=descriptor['bytes'] or hashlib.sha256(asset).hexdigest()!=descriptor['sha256']:raise ValueError('Image identity changed')
    if bitmap is not None:
        from . import emf_bitmap
        records=descriptor.get('native_emf',{}).get('bitmap_records',[])
        if type(bitmap) is not int or not 1<=bitmap<=len(records):raise ValueError('Embedded bitmap ordinal required')
        selected=dict(records[bitmap-1]);selected.pop('bitmap',None)
        pixels=emf_bitmap.decode(asset,selected);pixels.thumbnail((1600,1600))
        output=io.BytesIO();pixels.save(output,format='PNG');png=output.getvalue()
        if len(png)>10*1024*1024:raise ValueError('Preview byte limit')
        return png
    try:
        from .files import validate_image
        validate_image(asset)
        with Image.open(io.BytesIO(asset)) as original:
            if original.format not in {'PNG','JPEG','BMP','GIF','TIFF','WEBP'}:raise ValueError('Raster required')
            original.seek(0)
            pixels=original.convert('RGBA' if 'A' in original.getbands() or 'transparency' in original.info else 'RGB')
            pixels.thumbnail((1600,1600))
            output=io.BytesIO();pixels.save(output,format='PNG');png=output.getvalue()
            if len(png)>10*1024*1024:raise ValueError('Preview byte limit')
            return png
    except Exception:raise ValueError('Image preview unavailable; vector/invalid/oversized content needs separate review') from None


def render_preview(store,session_id,candidate_id):
    r=store.get_evidence(session_id,candidate_id);f=store.get_file(r['file_id'])
    if f['session_id']!=session_id or Path(f['name']).suffix.lower()!='.pdf':raise ValueError('PDF original in this conversation required')
    with Path(f['path']).open('rb') as stream:data=stream.read(100*1024*1024+1)
    digest=hashlib.sha256(data).hexdigest()
    if len(data)!=f['size'] or digest!=f['sha256'] or digest!=r['source_sha256']:raise ValueError('Original identity check failed')
    try:
        import fitz
        with fitz.open(stream=data,filetype='pdf') as pdf:
            number=r['page']
            if pdf.needs_pass or type(number) is not int or not 1<=number<=len(pdf):raise ValueError('Unavailable PDF page')
            page=pdf[number-1]
            width,height=page.rect.width,page.rect.height
            if not all(math.isfinite(v) and v>0 for v in (width,height)):raise ValueError('Invalid page geometry')
            rotation=page.rotation
            # Stored regions use unrotated coordinates, including offset CropBoxes.
            page.set_rotation(0)
            for box in (r.get('provenance') or {}).get('regions',[])[:100]:
                coords=[box[k] for k in ('left','top','right','bottom')]
                if not all(isinstance(v,(int,float)) and math.isfinite(v) for v in coords):raise ValueError('Invalid source region')
                region=fitz.Rect(*coords)
                if region.is_empty:raise ValueError('Invalid source region')
                page.draw_rect(region,color=(1,0,0),width=1.5,overlay=True)
            page.set_rotation(rotation)
            scale=min(1.5,1600/max(width,height))
            pixmap=page.get_pixmap(matrix=fitz.Matrix(scale,scale),colorspace=fitz.csRGB,alpha=False)
            if pixmap.width>1601 or pixmap.height>1601:raise ValueError('Preview exceeds pixel limit')
            png=pixmap.tobytes('png')
            if len(png)>10*1024*1024:raise ValueError('Preview exceeds byte limit')
            return png
    except Exception:raise ValueError('PDF preview unavailable; download original for separate review') from None


def render_original(store,session_id,file_id,number=1):
    """Authenticated project original, without registering a claim or changing bytes."""
    f=store.get_file(file_id)
    suffix=Path(f['name']).suffix.lower()
    if f['session_id']!=session_id or suffix not in {'.pdf','.png','.jpg','.jpeg'}:raise ValueError('Preview original in this conversation required')
    with Path(f['path']).open('rb') as stream:data=stream.read(100*1024*1024+1)
    if len(data)!=f['size'] or hashlib.sha256(data).hexdigest()!=f['sha256']:raise ValueError('Original identity check failed')
    try:
        import fitz
        with fitz.open(stream=data,filetype=suffix[1:]) as source:
            if suffix!='.pdf':
                from .files import validate_image
                validate_image(data)
                pdf=fitz.open('pdf',source.convert_to_pdf())
            else:pdf=source
            try:
                if pdf.needs_pass or type(number) is not int or not 1<=number<=len(pdf):raise ValueError('Unavailable original page')
                page=pdf[number-1];width,height=page.rect.width,page.rect.height
                if not all(math.isfinite(v) and v>0 for v in (width,height)):raise ValueError('Invalid page geometry')
                pixels=page.get_pixmap(matrix=fitz.Matrix(min(1.5,1600/max(width,height)),min(1.5,1600/max(width,height))),colorspace=fitz.csRGB,alpha=False)
                if max(pixels.width,pixels.height)>1601:raise ValueError('Preview pixel limit')
                png=pixels.tobytes('png')
                if len(png)>10*1024*1024:raise ValueError('Preview byte limit')
                return png
            finally:
                if pdf is not source:pdf.close()
    except Exception:raise ValueError('Original preview unavailable; download original for separate review') from None


def render_object_asset(payload,kind,bitmap=None):
    """Derived PNG of a selected passive OLE stream, never Word composition."""
    if kind!='embedded_object':raise ValueError('Embedded object required')
    from . import ole_bitmap
    import io
    from PIL import Image
    descriptor=ole_bitmap.describe(payload)
    records=descriptor.get('bitmaps',[])
    if bitmap is None:
        selected=None
    else:
        if type(bitmap) is not int or not 1<=bitmap<=len(records):raise ValueError('Object bitmap outside source')
        if records[bitmap-1]['status']!='AVAILABLE':raise ValueError('Object bitmap unavailable')
        selected=records[bitmap-1]['stream']
    png=ole_bitmap.render(payload,selected)
    with Image.open(io.BytesIO(png)) as pixels:
        pixels.thumbnail((1600,1600));out=io.BytesIO();pixels.save(out,format='PNG');result=out.getvalue()
    if len(result)>10*1024*1024:raise ValueError('Object preview byte limit')
    return result


def render_office_object(store,session_id,source_job,logical_unit,object_number,*,bitmap=1):
    from .source_binding import office_image_location
    from .office import Package,MAX_IMAGE_BYTES
    child=store.extraction_job(session_id,source_job)
    if len(child['file_ids'])!=1:raise ValueError('Single Office source required')
    file=store.get_file(child['file_ids'][0])
    if Path(file['name']).suffix.lower()!='.docx':raise ValueError('Native DOCX object required')
    binding=office_image_location(store,session_id,file,source_job,logical_unit)
    records=binding['locator'].get('embedded_objects',[])
    if type(object_number) is not int or not 1<=object_number<=len(records):raise ValueError('Object outside source element')
    descriptor=records[object_number-1]
    if descriptor['status']!='BOUND_PACKAGE_OBJECT':raise ValueError('Object bytes unavailable')
    with Path(file['path']).open('rb') as stream:data=stream.read(256*1024*1024+1)
    if len(data)!=file['size'] or hashlib.sha256(data).hexdigest()!=file['sha256']:raise ValueError('Office original identity changed')
    package=Package(data)
    try:
        if package.zip.getinfo(descriptor['part']).file_size>MAX_IMAGE_BYTES:raise ValueError('Object byte limit')
        asset=package.zip.read(descriptor['part'])
    finally:package.close()
    if len(asset)!=descriptor['bytes'] or hashlib.sha256(asset).hexdigest()!=descriptor['sha256']:raise ValueError('Object identity changed')
    return render_object_asset(asset,'embedded_object',bitmap)
