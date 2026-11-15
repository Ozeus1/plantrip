import io,tempfile,unittest
from pathlib import Path
from PIL import Image
import media_variants as mv

def jpeg(size,orientation=None):
    buf=io.BytesIO();img=Image.new('RGB',size,'red')
    exif=Image.Exif()
    if orientation:exif[0x0112]=orientation
    img.save(buf,'JPEG',quality=95,exif=exif.tobytes());return buf.getvalue()

class Variants(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.dir=Path(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()

    def test_resize_cache_orientation_and_drop(self):
        src=self.dir/'abc.jpg';src.write_bytes(jpeg((4000,3000),orientation=6))
        out=mv.variant(src,'image/jpeg',1280)
        self.assertEqual(out,self.dir/'variants'/'abc-1280.webp')
        with Image.open(out) as img:
            self.assertEqual(img.format,'WEBP')
            self.assertEqual(img.size,(960,1280),'EXIF 6 gira a foto para retrato e limita o lado maior')
        self.assertLess(out.stat().st_size,src.stat().st_size)
        stamp=out.stat().st_mtime_ns
        self.assertEqual(mv.variant(src,'image/jpeg',1280),out);self.assertEqual(out.stat().st_mtime_ns,stamp,'reaproveita o cache')
        mv.drop(src);self.assertFalse(out.exists())

    def test_falls_back_to_original(self):
        src=self.dir/'v.mp4';src.write_bytes(b'video')
        self.assertIsNone(mv.variant(src,'video/mp4',480))
        gif=self.dir/'a.gif';Image.new('RGB',(10,10)).save(gif)
        self.assertIsNone(mv.variant(gif,'image/gif',480),'GIF animado segue original')
        bad=self.dir/'bad.jpg';bad.write_bytes(b'not an image')
        self.assertIsNone(mv.variant(bad,'image/jpeg',480))
        ok=self.dir/'ok.jpg';ok.write_bytes(jpeg((100,80)))
        self.assertIsNone(mv.variant(ok,'image/jpeg',777),'só larguras permitidas')

if __name__=='__main__':unittest.main()
