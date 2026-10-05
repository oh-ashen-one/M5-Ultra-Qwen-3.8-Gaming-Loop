import datetime as dt
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from loop_controller.core import Store,Halt,read_json,atomic
from loop_controller.delivery_policy import FIRST_BUILD_UTC,HARD_CAP_EPOCH,HARD_CAP_UTC,apply_authorized_cap,deadline_guard,queue_milestone,preserve_closeout


class DeliveryPolicyTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.store=Store(self.root)
        self.store.set(started_epoch=HARD_CAP_EPOCH-200000,overall_deadline_epoch=HARD_CAP_EPOCH-100000,
            failure_streak=2,task_failures=5,diagnosis_used=True,last_verified_progress_epoch=111,
            source_checkpoint='candidate',last_playable_checkpoint='playable',next_task='retry')

    def tearDown(self):self.store.db.close();self.temp.cleanup()

    def test_cap_is_exactly_three_days_from_first_substantive_build(self):
        first=dt.datetime.fromisoformat(FIRST_BUILD_UTC).timestamp()
        self.assertEqual(HARD_CAP_EPOCH-first,3*24*3600)
        self.assertEqual(dt.datetime.fromtimestamp(HARD_CAP_EPOCH,dt.timezone.utc).isoformat(),HARD_CAP_UTC)

    def test_authorized_cap_does_not_reset_retry_or_progress_protections(self):
        before={k:self.store.get(k) for k in ('failure_streak','task_failures','diagnosis_used','last_verified_progress_epoch')}
        with patch('loop_controller.delivery_policy.time.time',return_value=HARD_CAP_EPOCH-100):
            config={};apply_authorized_cap(self.store,config)
        self.assertEqual(before,{k:self.store.get(k) for k in before})
        self.assertEqual(config['wall_hours']*3600,200000)
        self.assertEqual(self.store.get('superseded_overall_deadline_epoch'),HARD_CAP_EPOCH-100000)

    def test_no_work_at_or_after_cap_and_no_silent_extension(self):
        self.store.set(overall_deadline_epoch=HARD_CAP_EPOCH)
        deadline_guard(self.store,HARD_CAP_EPOCH-.01)
        for when in (HARD_CAP_EPOCH,HARD_CAP_EPOCH+1):
            with self.assertRaises(Halt):deadline_guard(self.store,when)
        self.store.set(overall_deadline_epoch=HARD_CAP_EPOCH+3600)
        with self.assertRaises(Halt):deadline_guard(self.store,HARD_CAP_EPOCH-1)

    def test_expired_migration_is_rejected(self):
        with patch('loop_controller.delivery_policy.time.time',return_value=HARD_CAP_EPOCH):
            with self.assertRaises(Halt):apply_authorized_cap(self.store,{})

    def test_milestone_keeps_actual_hash_and_confirmed_delivery_identity(self):
        bundle=self.root/'evidence/native';frame=bundle/'captures/frame-000.png';frame.parent.mkdir(parents=True)
        frame.write_bytes(b'actual-fixture-bytes')
        task={'id':'connected-mission'};gate={'passed':True,'candidate_commit':'abc','build_id':'def'}
        one=queue_milestone(self.store,'native-milestone',task,bundle,gate,[frame],{frame.name:3.2})
        self.assertFalse(one['public_upload']);self.assertEqual(one['visual_review'],'pending')
        path=self.root/'milestones/outbox/native--native-milestone.json'
        one['delivery_status']='delivered';one['library_files']=[{'library_file_id':'confirmed-id'}];atomic(path,one)
        two=queue_milestone(self.store,'native-milestone',task,bundle,gate,[frame],{frame.name:3.2},
                            {'verdict':'FIX','fixes':['Panel overlaps view']})
        self.assertEqual(two['library_files'],one['library_files'])
        self.assertEqual(two['delivery_status'],'delivered')
        self.assertEqual(two['visible_problems'],['Panel overlaps view'])
        self.assertEqual(len(two['frames'][0]['sha256']),64)

    def test_deadline_closeout_preserves_best_and_does_not_claim_quality(self):
        result=preserve_closeout(SimpleNamespace(store=self.store),'cap reached',True)
        self.assertEqual(result['saved_candidate'],'candidate')
        self.assertEqual(result['best_verified_playable_checkpoint'],'playable')
        self.assertFalse(result['new_work_allowed']);self.assertFalse(result['final_game_accepted'])
        self.assertEqual(read_json(self.root/'FINAL-HANDOFF.json'),result)


if __name__=='__main__':unittest.main()
