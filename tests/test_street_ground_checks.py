import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from loop_controller.street_ground_checks import PREFIX,SURFACES,probe,inspect_geometry,inspect_walkovers
from loop_controller.continuous_checks import validate_proposed
from continue_game_queue import review_captures
from loop_controller.core import Halt

class StreetGroundTests(unittest.TestCase):
    def geometry(self):
        before=[dict(name='WorldCollision/StreetPavement',kind='renderer',enabled=True,
                     boundsCenter=[41,.07,18],boundsSize=[38,.14,20])]
        added=[]
        for name,(center,size) in SURFACES.items():
            for kind in ('renderer','BoxCollider'):
                added.append(dict(name=PREFIX+name,kind=kind,enabled=True,boundsCenter=center.copy(),boundsSize=size.copy()))
        for i in range(9):
            added.append(dict(name=PREFIX+'LaneDash%02d'%i,kind='renderer',enabled=True,
                              boundsCenter=[26+4*i,.142,18],boundsSize=[2.4,.002,.10]))
        return before,before+added

    def test_geometry_requires_original_floor_and_matching_real_colliders(self):
        before,after=self.geometry();self.assertTrue(inspect_geometry(before,after)['passed'])
        for defect in ('raised-road','missing-collider','wrong-curb','dash-collider','floating-paint'):
            bad=copy.deepcopy(after)
            if defect=='raised-road':bad[0]['boundsCenter'][1]=.09
            if defect=='missing-collider':bad.pop(2)
            if defect=='wrong-curb':bad[5]['boundsSize'][1]=.6
            if defect=='dash-collider':bad[-1]['kind']='BoxCollider'
            if defect=='floating-paint':bad[-1]['boundsCenter'][1]=.4
            with self.subTest(defect=defect):self.assertFalse(inspect_geometry(before,bad)['passed'])

    def test_walkovers_need_both_actual_raised_supports_and_collision(self):
        rows=[]
        for first,y,z in [(37,.135,24),(38.8,.195,27),(45.5,.195,9)]:
            for i in range(6):
                rows.append(dict(time=first+i*.1,player=[53.5,y,z],mode='foot',grounded=True,
                                 playerCollisionEnabled=True,playerPenetration=0))
        self.assertTrue(inspect_walkovers(rows)['passed'])
        for defect in ('old-flat-floor','missing-south','disabled-collision'):
            bad=copy.deepcopy(rows)
            if defect=='old-flat-floor':
                for r in bad:r['player'][1]=.135
            if defect=='missing-south':bad=bad[:12]
            if defect=='disabled-collision':bad[0]['playerCollisionEnabled']=False
            with self.subTest(defect=defect):self.assertFalse(inspect_walkovers(bad)['passed'])

    def test_probe_preserves_all_mission_inputs_and_only_defers_external_reset(self):
        original=dict(duration=36,steps=[dict(start=4,end=5,keys=['W']),dict(start=32.5,end=32.8,keys=['F']),
            dict(start=34.002,end=34.302,keys=['R']),dict(start=35,end=35.3,keys=['F'])],captures=[3,15,31,32.55,34.6,35.6])
        before=copy.deepcopy(original);new=probe(original);self.assertEqual(original,before)
        self.assertEqual(new['steps'][:2],original['steps'][:2]);self.assertEqual(new['duration'],53)
        self.assertEqual([s['start'] for s in new['steps'] if 'R' in s['keys']],[50])
        validate_proposed(new,180,'mission-core')

    def test_scoped_review_uses_actual_requested_curb_frames_after_generic_selection(self):
        with tempfile.TemporaryDirectory() as temp:
            bundle=Path(temp);p=bundle/'captures';p.mkdir()
            times=[3,15,27.3234,38.8,45.5,50.6]
            (p/'scenario.json').write_text(json.dumps({'captures':times}))
            for i in range(len(times)):(p/('frame-%03d.png'%i)).touch()
            chosen,mapping=review_captures(dict(id='east-street-ground',review_frame_times=times[2:]),bundle)
            self.assertEqual(list(mapping.values()),times[2:])
            with self.assertRaises(Halt):review_captures(dict(id='east-street-ground',review_frame_times=[42]),bundle)
            with self.assertRaises(Halt):review_captures(dict(id='east-street-ground',review_frame_times=[38.8,38.8]),bundle)

    def test_install_recovery_accepts_only_the_exact_completed_two_statements(self):
        from unittest.mock import patch
        from loop_controller.core import sha
        import resume_saved_ground_install as saved
        old='            EastStreetDetail.Install(parent);\n'
        content='EastStreetDetail.Install(parent);\n            EastStreetGround.Install(parent);'
        def check(body,finish='stop'):
            raw=json.dumps({'choices':[{'finish_reason':finish,'message':{'content':body,'tool_calls':None}}]}).encode()
            with patch.object(saved,'RESPONSE_SHA',sha(raw)):return saved.saved_install(raw,old)
        self.assertEqual(check(content),content)
        for body in [content+'Destroy(parent);',content.replace('Ground','Other'),'Here is the edit: '+content]:
            with self.subTest(body=body),self.assertRaises(Halt):check(body)
        with self.assertRaises(Halt):check(content,'length')

if __name__=='__main__':unittest.main()
