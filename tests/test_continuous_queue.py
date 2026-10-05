"""Reject false passes and exercise real durable queue transitions without inference."""
import copy
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from loop_controller.core import Files,Halt,Store,atomic
from loop_controller.continuous_checks import evaluate_step,validate_proposed
from continue_game_queue import ContinuousRunner,ReadBoundEdits


class QueueTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.store=Store(self.root/'run');self.project=self.root/'project';self.project.mkdir()
        self.bundle=self.root/'evidence';(self.bundle/'captures').mkdir(parents=True)
        self.objects=[{'kind':'BoxCollider','enabled':True,'name':'wall'+str(i)} for i in range(6)]

    def tearDown(self):
        self.store.db.close();self.tmp.cleanup()

    def gate(self,checks,rows,objects=None):
        (self.bundle/'captures/trace.jsonl').write_text('\n'.join(json.dumps(r) for r in rows))
        atomic(self.bundle/'captures/scene-transforms.json',{'objects':objects or self.objects})
        return evaluate_step({'id':'fixture','checks':checks},self.bundle,{'passed':True,'duration':34})

    def test_held_world_input_must_stop_and_collider_must_stay_enabled(self):
        rows=[{'time':t,'player':[0,.135,29.6],'playerCollisionEnabled':True,'playerPenetration':0}
              for t in [14.5,15,15.8,21.5,22,22.8]]
        self.assertTrue(self.gate(['world_collision'],rows)['passed'])
        rows[-1]['player'][0]=2
        self.assertFalse(self.gate(['world_collision'],rows)['passed'])
        rows[-1]['player'][0]=0;rows[0]['playerCollisionEnabled']=False
        self.assertFalse(self.gate(['world_collision'],rows)['passed'])

    def test_vehicle_cannot_pass_by_driving_through_boundary_or_fake_reset(self):
        rows=[{'time':t,'mode':'vehicle','vehicle':[3.6,.14,27],
               'vehicleCollisionEnabled':True,'vehiclePenetration':0} for t in [16,17,17.8]]
        rows += [{'time':t,'mode':'foot','grounded':True,'restarts':1,
                  'player':[0,.135,1.7],'vehicle':[3.6,.14,8]} for t in [25,25.5,26]]
        rows += [{'time':t,'player':[0,.135,1.7+(t-27)*3]} for t in [27,28,29]]
        self.assertTrue(self.gate(['motor_reset'],rows)['passed'])
        rows[2]['vehicle'][2]=30
        self.assertFalse(self.gate(['motor_reset'],rows)['passed'])
        rows[2]['vehicle'][2]=27;rows[4]['vehicle']=[3.6,.14,27]
        self.assertFalse(self.gate(['motor_reset'],rows)['passed'])

    def test_mission_scope_is_distinct_from_combat_and_requires_actual_retry(self):
        rows=[{'time':4,'mission':'active','visibleText':['Objective: deliver'],'restarts':0},
              {'time':10,'mission':'failed','restarts':0},
              {'time':20,'mission':'active','restarts':1},
              {'time':30,'mission':'complete','restarts':1}]
        self.assertTrue(self.gate(['mission_complete','failure_retry'],rows)['passed'])
        rows[2]['restarts']=rows[3]['restarts']=0
        self.assertFalse(self.gate(['mission_complete','failure_retry'],rows)['passed'])

    def test_read_bound_edit_rejects_unread_span_and_concurrent_changes(self):
        files=Files(self.project,self.store);files.create('initial','Assets/Game/A.cs','line one\nline two\n')
        edits=ReadBoundEdits(files);fields={'path':'Assets/Game/A.cs','old':'line one','new':'changed'}
        with self.assertRaises(ValueError):edits.replace('unread',fields)
        edits.read(None,{'path':'Assets/Game/A.cs','line_count':1})
        with self.assertRaises(ValueError):edits.replace('outside-read',{**fields,'old':'line two'})
        (self.project/'Assets/Game/A.cs').write_text('line one\nconcurrent change\n')
        with self.assertRaisesRegex(ValueError,'Stale hash'):edits.replace('stale',fields)
        self.assertIn('concurrent change',(self.project/'Assets/Game/A.cs').read_text())

    def test_replay_cannot_remove_idle_preflight_or_set_gate_coverage(self):
        replay={'duration':40,'steps':[{'start':4,'end':8,'keys':['W']}],'captures':[3.2,10,20,30],
                'coverage':'fake'}
        self.assertEqual(validate_proposed(replay,60,'combat')['coverage'],'combat')
        replay['steps'][0]['start']=0
        with self.assertRaises(ValueError):validate_proposed(replay,60,'combat')
        replay['steps'][0]['start']=4;replay['duration']=float('nan')
        with self.assertRaises(ValueError):validate_proposed(replay,60,'combat')

    def test_pass_automatically_advances_without_stopping_owner(self):
        r=ContinuousRunner.__new__(ContinuousRunner);r.store=self.store
        r.machine=SimpleNamespace(guard=lambda:None);r.model=SimpleNamespace(ready=lambda:None)
        tasks=[{'id':n,'phase':'foundation','outcome':n,'probe':{}} for n in ('first','second')]
        seen=[]
        r.edit=lambda task,ident:seen.append(task['id']) or {'scenario':{'duration':20}}
        r.checkpoint_source=lambda _: 'candidate'
        r.native=lambda *args:(self.bundle,{'passed':True})
        r.regress=lambda *args:{'passed':True}
        r.review=lambda *args:{'ok':True,'verdict':'PASS'}
        def promote(task,*args):self.store.set(task_index=self.store.get('task_index',0)+1)
        r.promote=promote
        with patch('continue_game_queue.TASKS',tasks):r.work()
        self.assertEqual(seen,['first','second'])
        self.assertEqual(self.store.get('task_index'),2)
        self.assertEqual(self.store.get('status'),'reviewable-delivery')

    def test_repeated_blocker_diagnoses_then_restores_last_playable_without_resetting_history(self):
        r=ContinuousRunner.__new__(ContinuousRunner);r.store=self.store;r.project=self.project;r.repo=self.root
        self.store.set(last_playable_checkpoint='known-good')
        (self.project/'failed.cs').write_text('preserve this candidate')
        designs=[];r.design=lambda *a,**kw:designs.append(a)
        calls=[]
        with patch('continue_game_queue.git',side_effect=lambda *a:calls.append(a)),patch('continue_game_queue.subprocess.run') as run:
            for i in range(3):r.reject_scoped({'id':'collision'},str(i),{'failure':['blocked']},'failed-commit')
            self.assertEqual(len(designs),1)
            for i in range(2):r.reject_scoped({'id':'collision'},str(i+3),{'failure':['blocked']},'failed-commit')
            with self.assertRaisesRegex(Halt,'Repeated diagnosed blocker'):
                r.reject_scoped({'id':'collision'},'last',{'failure':['blocked']},'failed-commit')
        self.assertEqual((self.store.root/'failed-source/last/failed.cs').read_text(),'preserve this candidate')
        args=run.call_args.args[0]
        self.assertIn('restore',args);self.assertIn('known-good',args);self.assertNotIn('reset',args)
        self.assertEqual(self.store.get('last_playable_checkpoint'),'known-good')

if __name__=='__main__':unittest.main()
