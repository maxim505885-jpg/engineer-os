"""Source DIB payloads only: no GDI commands, crop, transforms or compositing."""
import hashlib
import struct

MAX_PIXELS=16000000
MAX_BITMAP_BYTES=32*1024*1024
MAX_BITMAP_RECORDS=512
COLOR_MASK_MODES={
    (32,0xff0000,0xff00,0xff):'BGRX',
    (16,0xf800,0x7e0,0x1f):'BGR;16',
    (16,0x7c00,0x3e0,0x1f):'BGR;15',
}


def record(data,offset,size,kind,ordinal):
    result=dict(record=ordinal,record_offset=offset,record_bytes=size,record_type=kind,
                status='UNAVAILABLE',scope='EMF_BITMAP_PAYLOAD_UNTRANSFORMED',content_verified=False,layout_verified=False)
    fixed=80 if kind==81 else 100
    if size<fixed:
        result['reason']='TRUNCATED_BITMAP_RECORD';return result
    bmi,cb,bits,length=struct.unpack_from('<4I',data,offset+(48 if kind==81 else 84))
    if not cb and not length:return None  # A source-free raster operation, not an embedded image.
    result.update(bmi_offset=offset+bmi,bmi_bytes=cb,bits_offset=offset+bits,bits_bytes=length)
    if (not cb or not length or bmi<fixed or bits<fixed or bmi%4 or bits%4 or
            bmi+cb>size or bits+length>size or (bmi<bits+length and bits<bmi+cb)):
        result['reason']='INVALID_BITMAP_SPANS';return result
    if cb not in {40,52} or struct.unpack_from('<I',data,offset+bmi)[0]!=40:
        result['reason']='UNSUPPORTED_DIB_HEADER';return result
    width,height,planes,depth,compression,image_bytes,xppm,yppm,colors,important=struct.unpack_from('<iiHH6I',data,offset+bmi+4)
    usage=struct.unpack_from('<I',data,offset+(64 if kind==81 else 80))[0]
    result.update(width=width,height=abs(height),top_down=height<0,bit_depth=depth,compression=compression,usage=usage,
                  raster_operation=struct.unpack_from('<I',data,offset+(68 if kind==81 else 40))[0])
    if planes!=1 or usage!=0 or colors or important:
        result['reason']='UNSUPPORTED_DIB_FORMAT';return result
    if compression==0:
        if cb!=40 or depth not in {24,32}:
            result['reason']='UNSUPPORTED_DIB_FORMAT';return result
    elif compression==3:
        if cb!=52 or depth not in {16,32}:
            result['reason']='UNSUPPORTED_DIB_FORMAT';return result
        masks=struct.unpack_from('<3I',data,offset+bmi+40);result['color_masks']=list(masks)
        for mask in masks:
            if not mask or mask>=(1<<depth):result['reason']='INVALID_COLOR_MASKS';return result
            channel=mask//(mask & -mask)
            if channel & (channel+1):result['reason']='INVALID_COLOR_MASKS';return result
        if any(masks[a]&masks[b] for a,b in [(0,1),(0,2),(1,2)]):
            result['reason']='INVALID_COLOR_MASKS';return result
        if (depth,*masks) not in COLOR_MASK_MODES:
            result['reason']='UNSUPPORTED_COLOR_MASKS';return result
    else:
        result['reason']='UNSUPPORTED_DIB_FORMAT';return result
    if width<=0 or not height or width*abs(height)>MAX_PIXELS or length>MAX_BITMAP_BYTES:
        result['reason']='BITMAP_PIXEL_OR_BYTE_LIMIT';return result
    stride=((width*depth+31)//32)*4
    if stride*abs(height)!=length:
        result['reason']='BITMAP_ROW_SIZE_MISMATCH';return result
    digest=hashlib.sha256();digest.update(memoryview(data)[offset+bmi:offset+bmi+cb]);digest.update(memoryview(data)[offset+bits:offset+bits+length])
    result.update(status='AVAILABLE',payload_sha256=digest.hexdigest(),stride=stride)
    return result


def decode(data,descriptor):
    from PIL import Image
    if descriptor.get('status')!='AVAILABLE':raise ValueError('Embedded bitmap unavailable')
    offset=descriptor['record_offset']
    if type(offset) is not int or offset<88 or offset>len(data)-8:raise ValueError('Invalid bitmap record offset')
    expected=dict(descriptor);expected.pop('bitmap',None)
    kind,size=struct.unpack_from('<II',data,offset)
    if kind not in {76,81} or size>len(data)-offset or record(data,offset,size,kind,descriptor['record'])!=expected:
        raise ValueError('Embedded bitmap identity changed')
    bits=descriptor['bits_offset'];length=descriptor['bits_bytes']
    mode=COLOR_MASK_MODES[(descriptor['bit_depth'],*descriptor['color_masks'])] if descriptor['compression']==3 else ('BGR' if descriptor['bit_depth']==24 else 'BGRX')
    return Image.frombytes('RGB',(descriptor['width'],descriptor['height']),data[bits:bits+length],
                           'raw',mode,descriptor['stride'],1 if descriptor['top_down'] else -1)
