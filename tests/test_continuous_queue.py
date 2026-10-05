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
from continue_game_queue import ContinuousRunner,ReadBoundEdits,review_captures
from recover_vehicle_entry import EntryRecovery,ENTRY_ANCHOR
from resume_inspected_queue import validate_resume


class QueueTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.store=Store(self.root/'run');self.project=self.root/'project';self.project.mkdir()
        self.bundle=self.root/'evidence';(self.bundle/'captures').mkdir(parents=True)
        self.objects=[{'kind':'BoxCollider','enabled':True,'name':'wall'+str(i)} for i in range(6)]

    def tearDown(self):
        self.store.db.close();self.tmp.cleanup()

    def test_inspection_resume_preserves_queue_and_rejects_unsafe_restart(self):
        state={'status':'paused','source_checkpoint':'verified','overall_deadline_epoch':200,
               'task_index':2,'failure_streak':2,'rounds':8}
        before=copy.deepcopy(state)
        marker='User requested live Unity GUI inspection. Preserve this pause; do not auto-restart.'
        pending=[{'kind':'model-request','id':'interrupted-planner'}]
        validate_resume(state,'verified','',marker,pending,100)
        self.assertEqual(state,before)
        cases=[({**state,'controller_pid':123},'verified','',marker,pending,100),
               (state,'changed','',marker,pending,100),
               (state,'verified',' M game/file.cs',marker,pending,100),
               (state,'verified','','unrelated pause',pending,100),
               (state,'verified','',marker,[{'kind':'edit'}],100),
               (state,'verified','',marker,pending,201)]
        for args in cases:
            with self.subTest(args=args),self.assertRaises(Halt):validate_resume(*args)

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
        rows += [{'time':t,'mode':'vehicle','vehicle':[3.6,.14,8],
                  'vehicleCollisionEnabled':True,'vehiclePenetration':0} for t in [7.5,7.7,7.9]]
        rows += [{'time':t,'mode':'foot','grounded':True,'player':[2,.135,27]} for t in [21.6,22,23]]
        self.assertTrue(self.gate(['motor_reset'],rows)['passed'])
        rows[2]['vehicle'][2]=30
        self.assertFalse(self.gate(['motor_reset'],rows)['passed'])
        rows[2]['vehicle'][2]=27;rows[4]['vehicle']=[3.6,.14,27]
        self.assertFalse(self.gate(['motor_reset'],rows)['passed'])

    def test_reset_cannot_hide_failed_early_entry_or_failed_E_exit(self):
        rows=[{'time':t,'mode':'vehicle','vehicle':[3.6,.14,27],
               'vehicleCollisionEnabled':True,'vehiclePenetration':0} for t in [16,17,17.8]]
        rows += [{'time':t,'mode':'foot','grounded':True,'restarts':1,
                  'player':[0,.135,1.7],'vehicle':[3.6,.14,8]} for t in [25,25.5,26]]
        rows += [{'time':t,'player':[0,.135,1.7+(t-27)*3]} for t in [27,28,29]]
        gate=self.gate(['motor_reset'],rows)
        self.assertIn('first-E-did-not-enter-before-throttle',gate['failure'])
        self.assertIn('E-exit-not-grounded-before-reset',gate['failure'])

    def test_failed_motion_reports_actual_input_mode_instead_of_guessing_physics(self):
        rows=[{'time':t,'mode':'foot','player':[3.15,.135,5.36],'vehicle':[3.36,0,7.96]}
              for t in [7.2,7.4,8,12,17]]
        (self.bundle/'captures/trace.jsonl').write_text('\n'.join(json.dumps(r) for r in rows))
        gate=evaluate_step({'id':'motor','checks':['motor_reset']},self.bundle,
                           {'passed':False,'failure':['vehicle-entry-and-motion']})
        self.assertFalse(gate['passed'])
        self.assertEqual(gate['input_observations'][1]['modes'],['foot'])

    def test_vehicle_review_includes_real_post_reset_frames_and_exact_times(self):
        for i in range(7):(self.bundle/'captures'/('frame-%03d.png'%i)).write_bytes(b'fixture')
        atomic(self.bundle/'captures/scenario.json',{'captures':[3.2,6.8,13,18.5,21.8,25,31]})
        frames,times=review_captures({'id':'vehicle-collision-reset'},self.bundle)
        self.assertEqual(len(frames),5)
        self.assertEqual(times['frame-003.png'],18.5)
        self.assertEqual(times['frame-005.png'],25)
        self.assertEqual(times['frame-006.png'],31)

    def test_entry_recovery_can_only_change_the_existing_condition(self):
        files=Files(self.project,self.store);path='Assets/Game/VehicleInteraction.cs'
        original='unchanged before\n'+ENTRY_ANCHOR+'\n    Enter();\nunchanged after\n'
        files.create('seed-entry',path,original)
        r=EntryRecovery.__new__(EntryRecovery);r.store=self.store;r.project=self.project;r.c={}
        def session(role,ident,system,prompt,tools,dispatch,**kw):
            self.assertEqual(kw['turns'],1);self.assertEqual(kw['reasoning_effort'],'low')
            self.assertEqual(list(dispatch),['edit_selected_span'])
            return dispatch['edit_selected_span']('exact-entry',{'content':'if (e && near_body)'})
        r.model=SimpleNamespace(session=session)
        result=r.edit({'id':'vehicle-collision-reset'},'one-line')
        self.assertTrue(result['ok']);self.assertTrue(self.store.get('entry_selected_edit_saved'))
        self.assertEqual((self.project/path).read_text(),original.replace(ENTRY_ANCHOR,'if (e && near_body)'))

    def test_mission_review_includes_captured_ending_between_drive_and_reset(self):
        times=[3.2,5.2,7.2,7.9,9.4,12.5,14,15.2,16.2,18.5]
        rows=[]
        for i,t in enumerate(times):
            (self.bundle/'captures'/('frame-%03d.png'%i)).write_bytes(b'fixture')
            carry=7.4<=t<14.3
            rows.append(dict(time=t,mission='complete' if 14.3<=t<17 else 'active',
                restarts=int(t>=17),missionObjects=[{'name':'Parcel','playerChild':carry}]))
        atomic(self.bundle/'captures/scenario.json',{'captures':times})
        (self.bundle/'captures/trace.jsonl').write_text('\n'.join(json.dumps(r) for r in rows))
        frames,mapping=review_captures({'id':'connected-mission','checks':['mission_complete']},self.bundle)
        self.assertEqual([p.name for p in frames],['frame-000.png','frame-003.png','frame-007.png','frame-009.png'])
        self.assertEqual(mapping['frame-007.png'],15.2)
        self.assertEqual(mapping['frame-009.png'],18.5)

    def test_mission_scope_is_distinct_from_combat_and_requires_actual_retry(self):
        rows=[]
        for t,z,carry,keys,mission,restarts in [(3,0,False,[],'active',0),(4,-2,False,['S'],'active',0),
                (5,1,False,['W'],'active',0),(6,1,True,['F'],'active',0),(10,1,True,[],'failed',0),
                (20,0,False,['R'],'active',1),(21,1,True,['F'],'active',1),(30,10,True,['F'],'complete',1)]:
            objects=[{'name':'Parcel','position':[0,0,z] if carry else [0,.5,2],'playerChild':carry},
                     {'name':'DropPad','position':[0,0,10],'playerChild':False},
                     {'name':'Beacon','position':[0,3,10],'playerChild':False}]
            rows.append(dict(time=t,player=[0,0,z],vehicle=[0,0,z],mission=mission,restarts=restarts,keys=keys,
                             mode='vehicle' if t==30 else 'foot',visibleText=['Objective: deliver'],missionObjects=objects))
        self.assertTrue(self.gate(['mission_complete','failure_retry'],rows)['passed'])
        for row in rows:row['restarts']=0
        self.assertFalse(self.gate(['mission_complete','failure_retry'],rows)['passed'])

    def test_mission_promotion_cannot_skip_anchor_gate(self):
        r=ContinuousRunner.__new__(ContinuousRunner)
        with self.assertRaisesRegex(Halt,'world-anchor'):
            r.promote({'checks':['mission_complete']},'candidate',self.bundle,{'passed':True},
                      {'ok':True,'verdict':'PASS'})

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

    def test_disjoint_reads_of_same_file_hash_remain_valid_until_a_save(self):
        files=Files(self.project,self.store);files.create('three-lines','Assets/Game/A.cs','one\ntwo\nthree\n')
        edits=ReadBoundEdits(files)
        edits.read(None,{'path':'Assets/Game/A.cs','start_line':1,'line_count':1})
        edits.read(None,{'path':'Assets/Game/A.cs','start_line':3,'line_count':1})
        edits.replace('earlier-valid-read',{'path':'Assets/Game/A.cs','old':'one','new':'first'})
        with self.assertRaisesRegex(ValueError,'Read the exact'):
            edits.replace('invalid-after-save',{'path':'Assets/Game/A.cs','old':'three','new':'third'})
    def test_pass_automatically_advances_without_stopping_owner(self):
        r=ContinuousRunner.__new__(ContinuousRunner);r.store=self.store
        r.machine=SimpleNamespace(guard=lambda:None);r.model=SimpleNamespace(ready=lambda:None)
        tasks=[{'id':n,'phase':'foundation','outcome':n,'probe':{'duration':20}} for n in ('first','second')]
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
