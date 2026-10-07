from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from seal_counter_exfil_preflight import union_support,validate_evidence,SOURCE,PRIOR
from loop_controller.core import Halt

class SurveyEvidenceTests(unittest.TestCase):
    def test_adjacent_renderers_cover_seam_but_real_gap_fails(self):
        point=dict(position=[0,0,0],groundY=.14,ground='physical pavement')
        def surface(x,width):
            return dict(name=str(x),kind='renderer',enabled=True,boundsCenter=[x,.07,0],boundsSize=[width,.14,2])
        self.assertTrue(union_support(point,dict(objects=[surface(-.5,1),surface(.5,1)]))['passed'])
        self.assertFalse(union_support(point,dict(objects=[surface(-.51,1),surface(.51,1)]))['passed'])
        self.assertFalse(union_support(dict(point,ground=None),dict(objects=[surface(0,2)]))['passed'])
    def test_only_static_capture_flag_is_scoped_out(self):
        gate=dict(candidate_commit=SOURCE,failure=['unchanging-captures'],build_exit=0,compile_errors=[],
            player_exit=0,build_id='real',scene_inventory=dict(passed=True))
        runtime=dict(errors=0,completed=True,duration=78,capture_id=PRIOR+'-survey')
        validate_evidence(gate,runtime,dict(time=77))
        for change in ({'errors':1},{'completed':False},{'capture_id':'different'}):
            with self.assertRaises(Halt):validate_evidence(gate,dict(runtime,**change),dict(time=77))
        with self.assertRaises(Halt):validate_evidence(dict(gate,failure=['unchanging-captures','runtime-errors']),runtime,dict(time=77))

if __name__=='__main__':unittest.main()
