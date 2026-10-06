import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from loop_controller.chapter_route_probe import pilot,measured_pose,corrected_turn,full_route,chapter_capture_selection
from loop_controller.continuous_checks import validate_proposed
from loop_controller.core import Halt
from resume_chapter_hud_route import validate_hud

ACTIVATION=dict(steps=[{'start':4.,'end':5.,'keys':['W']},{'start':14.3,'end':14.6,'keys':['F']},
                      {'start':17.,'end':17.3,'keys':['R']}])

class ChapterRouteProbeTests(unittest.TestCase):
    def test_only_normal_inputs_preserve_prefix_and_real_reset_after_completion(self):
        before=copy.deepcopy(ACTIVATION);probe,stop=pilot(ACTIVATION,1.6)
        self.assertEqual(ACTIVATION,before)
        self.assertFalse(any('R' in s['keys'] for s in probe['steps']))
        pose=dict(position=[12,0,16],forward=[1,0,0],yaw=90,error_degrees=0)
        route=full_route(ACTIVATION,1.6,pose);validate_proposed(route,180,'mission-core')
        self.assertFalse('fixture' in route)
        reset=next(s['start'] for s in route['steps'] if 'R' in s['keys'])
        self.assertGreater(reset,stop)
        self.assertTrue(any('E' in s['keys'] for s in route['steps']))
        self.assertEqual(route['steps'][:2],ACTIVATION['steps'][:2])

    def test_missing_exit_grounding_collisions_or_clear_bounds_fail_before_extrapolation(self):
        rows=[dict(time=t,mode='foot',grounded=True,restarts=0,vehicle=[12,0,16],
                   vehiclePhysics={'yaw':90,'forward':[1,0,0]}) for t in [25.,25.2,25.4]]
        rows.insert(0,dict(time=24,mode='vehicle',vehicleCollisionEnabled=True,vehiclePenetration=.01))
        self.assertEqual(measured_pose(rows,24.5)['error_degrees'],0)
        for key,value in [('grounded',False),('mode','vehicle'),('vehicle',[12,0,22])]:
            bad=copy.deepcopy(rows);bad[-1][key]=value
            with self.assertRaises(Halt):measured_pose(bad,24.5)
        bad=copy.deepcopy(rows);bad[0]['vehiclePenetration']=.8
        with self.assertRaises(Halt):measured_pose(bad,24.5)

    def test_heading_and_maneuver_limits_cannot_be_bypassed(self):
        with self.assertRaises(Halt):corrected_turn(2.4,50)
        with self.assertRaises(Halt):pilot(ACTIVATION,10)
        with self.assertRaises(Halt):
            full_route(ACTIVATION,1.6,dict(position=[12,0,16],forward=[.9,0,.4],yaw=65,error_degrees=25))

    def test_hud_scope_cannot_write_game_progress_or_hide_legacy_receipt(self):
        validate_hud('void LateUpdate() { if (RouteStage == 1) hud.text = "EAST DEAD-DROP"; }')
        for raw in ['RouteStage=2;','Cache = null;','LoopSignals.Mission = "complete";',
                    'void Update() {}','legacy.SetActive(false);','Destroy(player);']:
            with self.subTest(raw=raw),self.assertRaises(ValueError):validate_hud(raw)

    def test_review_selects_actual_handoff_junction_arrival_completion_and_reset(self):
        frames=[Path('frame-%03d.png'%i) for i in range(7)]
        rows=[]
        for i,(stage,x,mode,reset) in enumerate([(0,3,'foot',0),(1,1,'vehicle',0),(1,22,'vehicle',0),
                                               (1,47,'vehicle',0),(1,48,'foot',0),(2,48,'foot',0),(0,3,'foot',1)]):
            rows.append(dict(time=i,vehicle=[x,0,18],mode=mode,restarts=reset,routeChapter={'stage':stage}))
        selected=chapter_capture_selection(frames,{'captures':list(range(7))},rows)
        self.assertEqual(selected,[frames[i] for i in [1,2,3,5,6]])

if __name__=='__main__':unittest.main()

