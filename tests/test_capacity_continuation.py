import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from loop_controller.core import Halt,Store
from loop_controller.capacity_continuation import wait_until_admitted,CapacityContinuation
from loop_controller.delivery_policy import HARD_CAP_EPOCH

class CapacityContinuationTests(unittest.TestCase):
    def store(self, root):
        value=Store(root);self.addCleanup(value.db.close);return value

    def test_same_owner_is_visibly_yielded_then_resumes_without_resetting_history(self):
        with tempfile.TemporaryDirectory() as d:
            store=self.store(d);store.set(controller_pid=123,task_failures=24,source_checkpoint='qualified',overall_deadline_epoch=HARD_CAP_EPOCH)
            probes=iter([{'available':False},{'available':False},{'available':True}]);sleeps=[];guards=[]
            def sleep(seconds):
                self.assertEqual(store.get('status'),'capacity-wait');self.assertEqual(store.get('controller_pid'),123)
                self.assertEqual(store.get('capacity_resume_stage'),'native-inactive');sleeps.append(seconds)
            wait_until_admitted(store,lambda:guards.append(True),lambda:next(probes),'native-inactive',sleep)
            self.assertEqual(sleeps,[30,30]);self.assertEqual(len(guards),3)
            self.assertEqual(store.get('status'),'running');self.assertEqual(store.get('stage'),'native-inactive')
            self.assertEqual(store.get('task_failures'),24);self.assertEqual(store.get('source_checkpoint'),'qualified')
            self.assertEqual(store.get('overall_deadline_epoch'),HARD_CAP_EPOCH)

    def test_deadline_stop_or_resource_fault_precedes_any_further_admission(self):
        for reason in ['Three-day project cap reached','Requested stop','Memory/swap bound exceeded']:
            with self.subTest(reason=reason),tempfile.TemporaryDirectory() as d:
                store=self.store(d);calls=[]
                def guard():
                    if calls:raise Halt(reason)
                def probe():calls.append(True);return {'available':False}
                with self.assertRaisesRegex(Halt,reason):wait_until_admitted(store,guard,probe,'native',lambda _:None)
                self.assertEqual(len(calls),1)

    def test_capacity_interruption_archives_partial_bytes_before_one_new_native_attempt(self):
        with tempfile.TemporaryDirectory() as d:
            store=self.store(d);store.set(stage='native-inactive')
            runner=SimpleNamespace(store=store,machine=SimpleNamespace(child=None))
            coordinator=CapacityContinuation(runner);waits=[];coordinator.wait=lambda label:waits.append(label)
            bundle=Path(d)/'evidence'/'case';attempts=[]
            def native(project,target,scenario,candidate):
                target.mkdir(parents=True);attempts.append(True)
                if len(attempts)==1:
                    (target/'partial.log').write_text('original interrupted evidence')
                    raise Halt('Capacity wait: preserve other workload')
                return {'passed':True,'candidate_commit':candidate}
            result=coordinator.unity(native,Path(d),bundle,{},'qualified')
            self.assertTrue(result['passed']);self.assertEqual(len(waits),2)
            archives=list((Path(d)/'capacity-interruptions').glob('*/partial.log'))
            self.assertEqual(len(archives),1);self.assertEqual(archives[0].read_text(),'original interrupted evidence')

    def test_completed_evidence_and_noncapacity_faults_are_never_replayed(self):
        for completed in [True,False]:
            with self.subTest(completed=completed),tempfile.TemporaryDirectory() as d:
                store=self.store(d);runner=SimpleNamespace(store=store,machine=SimpleNamespace(child=None))
                coordinator=CapacityContinuation(runner);coordinator.wait=lambda _:None;bundle=Path(d)/'case';calls=[]
                def native(*args):
                    bundle.mkdir();calls.append(True)
                    if completed:(bundle/'gate.json').write_text('{"passed":true}')
                    raise Halt('Capacity wait: yielded' if completed else 'Memory/swap bound exceeded')
                with self.assertRaises(Halt):coordinator.unity(native,d,bundle,{},'qualified')
                self.assertEqual(len(calls),1);self.assertTrue(bundle.exists())

    def test_capacity_resume_requires_exact_checkpoint_and_cannot_repeat_or_extend_cap(self):
        from resume_hud_live_objective import validate_pause,CAPACITY_SOURCE,CAPACITY_ROUND,CAPACITY_BLOCKER,ACCEPTED
        state=dict(source_checkpoint=CAPACITY_SOURCE,last_playable_checkpoint=ACCEPTED,current_round=CAPACITY_ROUND,
            task_index=7,task_failures=24,failure_streak=1,diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,
            hud_live_objective_repair_attempted=True,blocker=CAPACITY_BLOCKER)
        validate_pause(state)
        for change in [{'hud_capacity_resume_attempted':True},{'overall_deadline_epoch':HARD_CAP_EPOCH+1},
                       {'source_checkpoint':'other'},{'task_failures':0}]:
            with self.subTest(change=change),self.assertRaises(Halt):validate_pause({**state,**change})

if __name__=='__main__':unittest.main()
