import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from loop_controller.mission_hud import inspect_courier_hud
from resume_mission_focus import observed_route
from loop_controller.replay_contract import validate_submission


class MissionHudTests(unittest.TestCase):
    def rows(self):
        rows=[]
        for t,state,carried,text,mode,keys,restarts in [
            (3,'active',False,'COURIER: grab the YELLOW parcel','foot',[],0),
            (7,'active',True,'COURIER: parcel in hand','foot',['F'],0),
            (14,'complete',False,'DELIVERY COMPLETE','vehicle',['F'],0),
            (17.1,'active',False,'COURIER: grab the YELLOW parcel','foot',['R'],1)]:
            rows.append(dict(time=t,mission=state,mode=mode,keys=keys,restarts=restarts,
                player=[0,.135,1.7],vehicle=[3.6,0,8],grounded=True,playerCollisionEnabled=True,
                visibleText=[text],missionObjects=[] if state=='complete' else
                [{'name':'Parcel','playerChild':carried,'position':[3.6,.5,3.2]}]))
        return rows

    def test_all_four_states_with_actual_reset(self):
        self.assertTrue(inspect_courier_hud(self.rows())['passed'])

    def test_completion_alone_is_not_retry_proof(self):
        self.assertFalse(inspect_courier_hud(self.rows()[:-1])['passed'])

    def test_fake_reset_or_early_carrying_is_rejected(self):
        for defect in ['keys','positions','parcel','hud','early-carry']:
            with self.subTest(defect=defect):
                rows=copy.deepcopy(self.rows())
                if defect=='keys':rows[-1]['keys']=[]
                if defect=='positions':rows[-1]['player']=[0,0,20]
                if defect=='parcel':rows[-1]['missionObjects'][0]['playerChild']=True
                if defect=='hud':rows[-1]['visibleText']=['parcel in hand']
                if defect=='early-carry':rows[0]['visibleText']=['parcel in hand']
                self.assertFalse(inspect_courier_hud(rows)['passed'])

    def test_supplied_route_preserves_observed_inputs_and_adds_reset(self):
        previous={'steps':[{'start':4,'end':5,'keys':['W']} ]}
        fixture=observed_route(previous)
        result=validate_submission(fixture,{'maximum':150,'coverage':'mission-core'})
        self.assertEqual(result['scenario']['steps'][0],previous['steps'][0])
        self.assertEqual(result['scenario']['steps'][-1]['keys'],['R'])


if __name__=='__main__':unittest.main()
