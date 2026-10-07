import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from repair_character_clip_api import apply_patches,exact_spans
from loop_controller.core import Halt

class CharacterAPIPatches(unittest.TestCase):
    source='import bpy\nprotected_geometry = 5\ndef keyrot(n,f,r):\n    pass\nALLP=[]\nfor n in ALLP:\n    pass\nprotected_pose=8\n'
    def response(self,patches,finish='stop'):
        return dict(choices=[dict(finish_reason=finish,message=dict(content=json.dumps(dict(replacements=patches))))])
    def test_only_exact_two_completed_spans_are_writable(self):
        spans=exact_spans(self.source)
        patches=[dict(old=x,new=x.replace('pass','a=1')) for x in spans]
        result=apply_patches(self.source,self.response(patches))
        self.assertIn('protected_geometry = 5',result);self.assertIn('protected_pose=8',result)
        with self.assertRaises(Halt):apply_patches(self.source,self.response(patches,'length'))
        patches[0]['old']='protected_geometry = 5\n'
        with self.assertRaises(Halt):apply_patches(self.source,self.response(patches))

if __name__=='__main__':unittest.main()
