import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from loop_controller.review_summary import critic_evidence,require_combat_contracts
from loop_controller.combat_checks import inspect_combat_contract


class ReviewSummaryTests(unittest.TestCase):
    def test_summary_keeps_failure_and_damage_attribution_without_repeated_samples(self):
        gate={'passed':True,'combat_contracts':[dict(scope='driving',facts={
            'escape_samples':[dict(time=i/10,pursuit=0) for i in range(1000)],
            'pursuit_transitions':[dict(level=0),dict(level=3),dict(level=0)],
            'player_shot_rival_damage_events':[dict(rival_hp_before=3,rival_hp_after=2)]})],
            'regressions':{'passed':False,'failure':['specific-failure'],'regressions':[
                {'test':'motor','gate':{'passed':False,'failure':['real-wall'],'diagnostic':'x'*50000}}]}}
        value=critic_evidence(gate)
        self.assertLess(len(json.dumps(value)),2000)
        self.assertEqual(value['regressions']['tests'][0]['failure'],['real-wall'])
        facts=value['combat_contracts'][0]['facts']
        self.assertEqual(facts['pursuit_transitions'][1]['level'],3)
        self.assertEqual(facts['player_shot_rival_damage_events'][0]['rival_hp_after'],2)
        self.assertEqual(len(gate['combat_contracts'][0]['facts']['escape_samples']),1000)

    def test_promotion_requires_three_current_source_contracts_and_stable_escape(self):
        gate={'candidate_commit':'source','combat_contracts':[dict(scope=s,passed=True,candidate='source',
            facts={'longest_continuous_escape_seconds':5}) for s in ['foot','wall','driving']]}
        self.assertTrue(require_combat_contracts(gate))
        gate['combat_contracts'][-1]['facts']['longest_continuous_escape_seconds']=.1
        self.assertFalse(require_combat_contracts(gate))
        gate['combat_contracts'][-1]['facts']['longest_continuous_escape_seconds']=5
        gate['combat_contracts'][0]['candidate']='old-source'
        self.assertFalse(require_combat_contracts(gate))

    def test_real_rival_hp_drop_is_separate_from_enemy_damage(self):
        def row(t,hp,health,hits,keys):return dict(time=t,health=health,hits=hits,shots=hits,keys=keys,
            pursuit=3,mode='foot',rivals=[dict(hp=hp,alive=True,renderers=1,renderSize=[.7,1.57,.5],
            actorDistance=3,attackUnobstructed=True,firstAttackCollider='Player',firstAimCollider='Rival')])
        rows=[row(7.4,3,100,0,[]),row(7.53,2,96,1,['Mouse0'])]
        result=inspect_combat_contract(rows,'foot');self.assertTrue(result['passed'])
        self.assertEqual(result['facts']['damage_events'][0]['collider'],'Player')
        self.assertEqual(result['facts']['player_shot_rival_damage_events'][0]['rival_hp_after'],2)
        rows[-1]['rivals'][0]['hp']=3
        self.assertIn('actual-rival-hp-damage-not-exercised',inspect_combat_contract(rows,'foot')['failure'])


if __name__=='__main__':unittest.main()
