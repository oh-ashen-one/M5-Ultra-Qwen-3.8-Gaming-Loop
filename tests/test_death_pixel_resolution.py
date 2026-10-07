from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import resolve_death_pixel_review as m
from PIL import Image


class PixelResolutionTests(unittest.TestCase):
    def test_empty_or_changed_masks_cannot_clear_disagreement(self):
        with tempfile.TemporaryDirectory() as folder:
            a=Path(folder)/'early.png';b=Path(folder)/'late.png'
            im=Image.new('RGB',(960,540))
            im.save(a);im.save(b)
            self.assertFalse(m.compare_masks(a,b)['passed'])
            positions=[(x,y) for y in range(30,124) for x in range(420,810)][:1831]
            for point in positions:im.putpixel(point,(255,65,56))
            im.save(a);im.save(b)
            self.assertTrue(m.compare_masks(a,b)['passed'])
            im.putpixel(positions[0],(0,0,0));im.save(b)
            result=m.compare_masks(a,b)
            self.assertFalse(result['passed'])
            self.assertEqual(result['first_only'],1)

    def test_pass_requires_correct_death_and_reset_attribution(self):
        fields=dict(verdict='PASS',summary=m.DEATH+' at75.65s and '+m.RESET+' at79.4s are clear.',
            fixes=[],death_frame=m.DEATH,death_health=0,reset_frame=m.RESET,reset_health=100)
        self.assertEqual(m.confirm_review(fields)['verdict'],'PASS')
        for changes in ({'death_frame':m.RESET},{'reset_frame':'courier-pickup/frame-001.png'},
                {'death_health':100},{'reset_health':0}):
            with self.subTest(changes=changes),self.assertRaises(ValueError):
                m.confirm_review(dict(fields,**changes))
        self.assertEqual(m.confirm_review(dict(fields,verdict='FIX',fixes=['Unreadable actual reset']))['verdict'],'FIX')


if __name__=='__main__':unittest.main()

