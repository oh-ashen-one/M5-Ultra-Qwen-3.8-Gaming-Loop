from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from inspect_combat_contracts import summarize_combat
from loop_controller.combat_checks import inspect_combat_contract
from qualify_combat_focus import combined_probe,CombatFocus,VISUAL_REPAIRED,REPAIRED,ACCEPTED
from loop_controller.core import Halt
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.continuous_checks import validate_proposed


class CombatObservationTests(unittest.TestCase):
    def test_resume_preserves_exact_partial_source_and_rejects_unrelated_failures(self):
        old=dict(task_index=4,source_checkpoint=VISUAL_REPAIRED,last_playable_checkpoint=ACCEPTED,
            task_failures=0,failure_streak=0,overall_deadline_epoch=HARD_CAP_EPOCH,
            blocker='Halt: Local combat edit saved no change: chase-and-occluded-attack',
            combat_selected_edits=['preserve-imported-visual-basis','rival-pavement-height'],
            combat_before_contracts=[dict(scope='foot'),dict(scope='wall')])
        CombatFocus.validate_recovery(None,old)
        for changes in [dict(source_checkpoint='other'),dict(task_failures=1),dict(failure_streak=1),
                        dict(blocker='different fault'),dict(combat_before_contracts=[])]:
            with self.assertRaises(Halt):CombatFocus.validate_recovery(None,{**old,**changes})
        drive={**old,'source_checkpoint':REPAIRED,'task_failures':1,'failure_streak':1,
            'blocker':'Halt: Measured combat contract failure; preserve candidate and diagnose exact observations',
            'feedback':{'failure':['driving-escape-distance-not-exercised']}}
        CombatFocus.validate_recovery(None,drive)
        CombatFocus.validate_recovery(None,{**drive,'task_failures':2,'failure_streak':2})
        for changes in [dict(task_failures=3),dict(feedback={'failure':['damage-through-wall']}),
                        dict(source_checkpoint='other')]:
            with self.assertRaises(Halt):CombatFocus.validate_recovery(None,{**drive,**changes})

    def test_damage_and_pursuit_use_actual_vehicle_distance_in_diagnostic(self):
        rows=[]
        for t,hp in [(10,100),(12,96)]:
            rows.append(dict(time=t,mode='vehicle',health=hp,pursuit=3,restarts=0,
                rivals=[dict(alive=True,actorDistance=23,footDistance=3,attackUnobstructed=False,firstAttackCollider='wall')]))
        facts=summarize_combat(rows)
        self.assertEqual(facts['pursuit_while_vehicle_over_18m'],[3])
        self.assertEqual(facts['damage_events'][0]['actor_distance'],23)
        self.assertFalse(facts['damage_events'][0]['unobstructed'])
        self.assertFalse(facts['gameplay_acceptance_claimed'])

    def rows(self):
        return [dict(time=7.1+i*.1,mode='foot',health=100,shots=int(i>3),hits=0,pursuit=3,restarts=0,
            keys=['Mouse0'] if 4<=i<=6 else [],rivals=[dict(alive=True,hp=3,renderers=22,renderSize=[.7,1.57,.5],
            actorDistance=3,footDistance=3,attackUnobstructed=False,firstAttackCollider='CombatValidationWall',
            firstAimCollider='CombatValidationWall',position=[0,0,0])]) for i in range(20)]

    def test_real_wall_must_block_both_sides_and_have_positive_test_coverage(self):
        rows=self.rows();self.assertTrue(inspect_combat_contract(rows,'wall')['passed'])
        rows[-1]['health']=96
        self.assertIn('enemy-damages-through-nearer-wall',inspect_combat_contract(rows,'wall')['failure'])
        rows[-1]['hits']=1;rows[-1]['rivals'][0]['hp']=2
        self.assertIn('player-damages-rival-through-nearer-wall',inspect_combat_contract(rows,'wall')['failure'])
        for row in rows:row['rivals'][0]['firstAimCollider']='different'
        self.assertIn('real-wall-occlusion-not-exercised',inspect_combat_contract(rows,'wall')['failure'])

    def test_tiny_or_flat_imported_visual_is_rejected_even_with_normal_collider(self):
        rows=self.rows();rows[0]['rivals'][0]['renderSize']=[.007,.016,.004]
        self.assertIn('rival-import-basis-or-visible-scale-invalid',inspect_combat_contract(rows,'wall')['failure'])

    def test_driving_pursuit_and_damage_cannot_use_near_inactive_foot_actor(self):
        rows=self.rows()
        for i,row in enumerate(rows):
            row.update(mode='vehicle',pursuit=0)
            row['rivals'][0].update(actorDistance=23,position=[0,0,i*.2])
        self.assertTrue(inspect_combat_contract(rows,'driving')['passed'])
        rows[-1].update(pursuit=3,health=96)
        failures=inspect_combat_contract(rows,'driving')['failure']
        self.assertIn('pursuit-does-not-follow-actual-vehicle-distance',failures)
        self.assertIn('damage-outside-actual-controlled-actor-range',failures)

    def test_combined_replay_preserves_the_accepted_input_route_after_real_reset(self):
        prior=dict(steps=[dict(start=4,end=5,keys=['W']),dict(start=14.3,end=14.6,keys=['F'])])
        probe=combined_probe(prior)
        self.assertEqual(probe['steps'][-1],dict(start=30.8,end=31.1,keys=['F']))
        self.assertTrue(any(s['keys']==['R'] and s['start']==16.5 for s in probe['steps']))
        self.assertEqual(validate_proposed(probe,180,'combat')['coverage'],'combat')


if __name__=='__main__':unittest.main()
