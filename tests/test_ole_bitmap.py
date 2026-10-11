import hashlib
import io
import struct
import unittest
from unittest.mock import patch

from PIL import Image
try:
    from engineering.local_app import ole_bitmap
except ImportError:
    ole_bitmap = None
try:
    import olefile
except ImportError:
    olefile = None


def bmp(width=40, height=40):
    stride=((width*24+31)//32)*4
    bits=(b'\x00\x00\xff'*width+b'\x00'*(stride-width*3))*abs(height)
    dib=struct.pack('<IiiHH6I',40,width,height,1,24,0,len(bits),0,0,0,0)+bits
    return struct.pack('<2sIHHI',b'BM',14+len(dib),0,0,54)+dib


def compound(streams):
    """Small real CFB v3 fixture using regular sectors, never a fake parser."""
    end,free,fatmark=0xfffffffe,0xffffffff,0xfffffffd
    sector_data=[]; entries=[];links=[fatmark,end]
    for name,raw in streams:
        if len(raw)<4096:raise ValueError('Fixture streams use regular FAT')
        start=2+len(sector_data);count=(len(raw)+511)//512
        for n in range(count):
            sector_data.append(raw[n*512:(n+1)*512].ljust(512,b'\x00'))
            links.append(start+n+1 if n<count-1 else end)
        entries.append((name,start,len(raw)))
    header=bytearray(512);header[:8]=bytes.fromhex('d0cf11e0a1b11ae1')
    struct.pack_into('<HHHHH',header,24,0x3e,3,0xfffe,9,6)
    struct.pack_into('<9I',header,40,0,1,1,0,4096,end,0,end,0)
    struct.pack_into('<109I',header,76,0,*([free]*108))
    def entry(name,kind,child,left,right,start,size):
        d=bytearray(128);encoded=(name+'\x00').encode('utf-16-le');d[:len(encoded)]=encoded
        struct.pack_into('<HBBIII',d,64,len(encoded),kind,1,left,right,child)
        struct.pack_into('<IQ',d,116,start,size);return bytes(d)
    directory=[entry('Root Entry',5,1,free,free,end,0)]
    for n,(name,start,size) in enumerate(entries):
        directory.append(entry(name,2,free,free,n+2 if n<len(entries)-1 else free,start,size))
    return bytes(header)+struct.pack('<128I',*(links+[free]*(128-len(links))))+b''.join(directory).ljust(512,b'\x00')+b''.join(sector_data)


class OleBitmapTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(ole_bitmap,'Bounded source OLE bitmap decoder must exist')

    def test_optional_dependency_unavailable_is_explicit(self):
        with patch.dict('sys.modules',{'olefile':None}):
            d=ole_bitmap.describe(compound([('CONTENTS',bmp())]))
        self.assertEqual((d['status'],d['reason']),('UNAVAILABLE','OLEFILE_UNAVAILABLE'))
        self.assertFalse(d['content_verified'])

    def test_invalid_compound_and_source_byte_limit_fail_closed(self):
        for raw in (b'not compound',bytes.fromhex('d0cf11e0a1b11ae1')+b'\x00'*504):
            d=ole_bitmap.describe(raw)
            self.assertEqual(d['status'],'UNAVAILABLE')
        with patch.object(ole_bitmap,'MAX_OLE_BYTES',20):
            self.assertEqual(ole_bitmap.describe(b'x'*21)['reason'],'OLE_BYTE_LIMIT')

    @unittest.skipUnless(olefile,'Optional olefile not installed')
    def test_native_bitmap_exact_span_hash_and_pixels(self):
        raw=bmp();stream=struct.pack('<I',len(raw)+10)+raw+b'\x00'*10
        data=compound([('\x01Ole10Native',stream)]);old=hashlib.sha256(data).hexdigest()
        d=ole_bitmap.describe(data);self.assertEqual(d['status'],'AVAILABLE')
        b=d['bitmaps'][0]
        self.assertEqual(b['stream'],['\x01Ole10Native'])
        self.assertEqual((b['bitmap_offset'],b['bitmap_bytes']),(4,len(raw)))
        self.assertEqual(b['stream_sha256'],hashlib.sha256(stream).hexdigest())
        self.assertEqual(b['bitmap_sha256'],hashlib.sha256(raw).hexdigest())
        self.assertEqual(ole_bitmap.extract(data),raw)
        image=Image.open(io.BytesIO(ole_bitmap.render(data)))
        self.assertEqual((image.size,image.getpixel((0,0))),((40,40),(255,0,0)))
        self.assertEqual(hashlib.sha256(data).hexdigest(),old)
        self.assertFalse(d['content_verified']);self.assertFalse(d['layout_verified'])

    @unittest.skipUnless(olefile,'Optional olefile not installed')
    def test_contents_dib_and_top_down_bmp_render(self):
        for raw,kind in ((bmp()[14:],'DIB'),(bmp(height=-40),'BMP')):
            data=compound([('CONTENTS',raw)]);d=ole_bitmap.describe(data)
            self.assertEqual(d['bitmaps'][0]['format'],kind)
            self.assertEqual(ole_bitmap.extract(data,['CONTENTS']),raw)
            self.assertEqual(Image.open(io.BytesIO(ole_bitmap.render(data,'CONTENTS'))).getpixel((0,0)),(255,0,0))

    @unittest.skipUnless(olefile,'Optional olefile not installed')
    def test_multicolor_rows_preserve_orientation_and_bgr_channels_24_32_bit(self):
        width,height=41,40  # 24-bit rows have padding; 32-bit rows have X bytes.
        rows=[bytes(channel for x in range(width) for channel in
                    ((17*x+3*y)%256,(5*x+11*y+19)%256,(7*x+23*y+101)%256))
              for y in range(height)]
        expected=b''.join(rows)
        for depth in (24,32):
            for top_down in (False,True):
                with self.subTest(bit_depth=depth,top_down=top_down):
                    stride=((width*depth+31)//32)*4
                    encoded_rows=[]
                    for row in rows if top_down else reversed(rows):
                        pixels=bytearray()
                        for offset in range(0,len(row),3):
                            red,green,blue=row[offset:offset+3]
                            pixels.extend((blue,green,red))
                            if depth==32:pixels.append(37)  # BGRX ignores this byte.
                        encoded_rows.append(bytes(pixels).ljust(stride,b'\xa5'))
                    bits=b''.join(encoded_rows)
                    dib=struct.pack('<IiiHH6I',40,width,-height if top_down else height,
                                    1,depth,0,len(bits),0,0,0,0)+bits
                    raw=struct.pack('<2sIHHI',b'BM',14+len(dib),0,0,54)+dib
                    data=compound([('CONTENTS',raw)])
                    descriptor=ole_bitmap.describe(data)['bitmaps'][0]
                    self.assertEqual((descriptor['bit_depth'],descriptor['top_down']),
                                     (depth,top_down))
                    with Image.open(io.BytesIO(ole_bitmap.render(data,'CONTENTS'))) as rendered:
                        self.assertEqual((rendered.mode,rendered.size),('RGB',(width,height)))
                        self.assertEqual(rendered.tobytes(),expected)

    @unittest.skipUnless(olefile,'Optional olefile not installed')
    def test_huge_pixel_bomb_rejected_before_pillow(self):
        raw=bytearray(bmp());struct.pack_into('<ii',raw,18,100000,100000)
        data=compound([('CONTENTS',bytes(raw))])
        with patch('PIL.Image.frombytes',side_effect=AssertionError('Must not decode')):
            d=ole_bitmap.describe(data)
            self.assertEqual(d['status'],'UNAVAILABLE')
            self.assertEqual(d['bitmaps'][0]['reason'],'BITMAP_PIXEL_OR_BYTE_LIMIT')
            with self.assertRaises(ValueError):ole_bitmap.render(data)

    @unittest.skipUnless(olefile,'Optional olefile not installed')
    def test_invalid_native_length_and_truncated_bits_rejected(self):
        raw=bmp()
        for stream in (struct.pack('<I',len(raw)+1)+raw,struct.pack('<I',len(raw)-1)+raw):
            data=compound([('\x01Ole10Native',stream)])
            if len(stream)!=struct.unpack_from('<I',stream)[0]+4:
                self.assertEqual(ole_bitmap.describe(data)['status'],'UNAVAILABLE')
        bad=raw[:-8]
        self.assertEqual(ole_bitmap.describe(compound([('CONTENTS',bad)]))['status'],'UNAVAILABLE')

    @unittest.skipUnless(olefile,'Optional olefile not installed')
    def test_multiple_bitmaps_require_explicit_stream_and_bounds(self):
        raw=bmp();native=struct.pack('<I',len(raw))+raw
        data=compound([('CONTENTS',raw),('\x01Ole10Native',native)])
        self.assertEqual(len(ole_bitmap.describe(data)['bitmaps']),2)
        with self.assertRaises(ValueError):ole_bitmap.render(data)
        self.assertTrue(ole_bitmap.render(data,'CONTENTS').startswith(b'\x89PNG'))
        with self.assertRaises(ValueError):ole_bitmap.render(data,'../CONTENTS')
        with patch.object(ole_bitmap,'MAX_STREAMS',1):
            self.assertEqual(ole_bitmap.describe(data)['reason'],'OLE_STREAM_LIMIT')
        with patch.object(ole_bitmap,'MAX_STREAM_BYTES',10):
            self.assertEqual(ole_bitmap.describe(data)['reason'],'OLE_STREAM_BYTE_LIMIT')
        with patch.object(ole_bitmap,'MAX_TOTAL_STREAM_BYTES',len(raw)+1):
            self.assertEqual(ole_bitmap.describe(data)['reason'],'OLE_STREAM_BYTE_LIMIT')

    @unittest.skipUnless(olefile,'Optional olefile not installed')
    def test_malicious_minifat_and_oversized_root_rejected(self):
        valid=compound([('CONTENTS',bmp())])
        for field,value in ((64,0xffffffff),(60,0xfffffffd),(1024+120,1<<40)):
            malformed=bytearray(valid)
            struct.pack_into('<Q' if field==1024+120 else '<I',malformed,field,value)
            self.assertEqual(ole_bitmap.describe(bytes(malformed))['status'],'UNAVAILABLE')

    @unittest.skipUnless(olefile,'Optional olefile not installed')
    def test_unknown_package_never_executes_or_signature_scans(self):
        raw=(b'not bitmap'+bmp()).ljust(5000,b'\x00')
        d=ole_bitmap.describe(compound([('package.exe',raw)]))
        self.assertEqual(d['status'],'UNAVAILABLE')
        self.assertEqual(d['reason'],'NO_SUPPORTED_BITMAP_STREAM')

    @unittest.skipUnless(olefile,'Optional olefile not installed')
    def test_directory_cycle_and_duplicate_names_fail_closed(self):
        raw=bmp();data=bytearray(compound([('CONTENTS',raw)]))
        # stream directory entry links itself: reject before library recursion.
        struct.pack_into('<I',data,1024+128+72,1)
        self.assertEqual(ole_bitmap.describe(bytes(data))['status'],'UNAVAILABLE')
        duplicated=compound([('CONTENTS',raw),('contents',raw)])
        self.assertEqual(ole_bitmap.describe(duplicated)['status'],'UNAVAILABLE')


if __name__=='__main__':unittest.main()
