import contextlib
import fcntl
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from shared_capture_slots import capture_slots


class CaptureSlotsTests(unittest.TestCase):
    def base(self,d):
        p=Path(d)
        for name in ('locks','holders','queue'): (p/name).mkdir()
        for name in ('perf.lock','capture.0.lock','capture.1.lock'): (p/'locks'/name).touch()
        return p

    def hold(self,p,name,mode=fcntl.LOCK_EX):
        f=(p/'locks'/name).open('r+');fcntl.flock(f,mode|fcntl.LOCK_NB)
        self.addCleanup(f.close);return f

    def test_authorized_priority_uses_free_slot_preserves_other_holder_and_queue(self):
        with tempfile.TemporaryDirectory() as d:
            p=self.base(d);self.hold(p,'capture.0.lock');self.hold(p,'perf.lock',fcntl.LOCK_SH)
            foreign=p/'holders/foreign.json';foreign.write_text('{"pid":123,"slot":"0"}')
            queue=p/'queue/other.json';queue.write_text('{"pid":456}')
            checks=[]
            with capture_slots(p,{'label':'owned'},external_renderers=8,coexistence=True,guard=lambda:checks.append(True)):
                holder=json.loads((p/'holders'/f'{os.getpid()}.json').read_text())
                self.assertEqual(holder['reserved_slots'],[1]);self.assertEqual(len(checks),2)
                self.assertEqual(foreign.read_text(),'{"pid":123,"slot":"0"}')
                self.assertEqual(queue.read_text(),'{"pid":456}')
            self.assertEqual(list((p/'holders').iterdir()),[foreign])

    def test_exclusive_performance_or_two_real_slot_holders_block(self):
        for reason in ('performance','two-slots'):
            with self.subTest(reason=reason),tempfile.TemporaryDirectory() as d:
                p=self.base(d)
                names=['perf.lock'] if reason=='performance' else ['capture.0.lock','capture.1.lock']
                for name in names:self.hold(p,name)
                with self.assertRaises((BlockingIOError,RuntimeError)):
                    with capture_slots(p,{},coexistence=True,guard=lambda:None):self.fail('must not enter')
                self.assertFalse(list((p/'holders').iterdir()))

    def test_pause_and_resource_fault_are_not_waived(self):
        for reason in ('paused','memory','swap','thermal','ownership'):
            with self.subTest(reason=reason),tempfile.TemporaryDirectory() as d:
                p=self.base(d)
                if reason=='paused':(p/'PAUSED').touch()
                def guard():
                    if reason=='ownership':return False
                    if reason!='paused':raise RuntimeError(reason)
                with self.assertRaises(RuntimeError):
                    with capture_slots(p,{},coexistence=True,guard=guard):self.fail('must not enter')
                self.assertFalse(list((p/'holders').iterdir()))

    def test_second_guard_failure_releases_our_locks_and_no_authorization_keeps_old_policy(self):
        with tempfile.TemporaryDirectory() as d:
            p=self.base(d);calls=[]
            def guard():
                calls.append(True)
                if len(calls)==2:raise RuntimeError('resource changed during acquisition')
            with self.assertRaises(RuntimeError):
                with capture_slots(p,{},coexistence=True,guard=guard):pass
            with capture_slots(p,{},coexistence=True,guard=lambda:None):pass
            (p/'queue/foreign').touch()
            with self.assertRaisesRegex(RuntimeError,'waiters'):
                with capture_slots(p,{},external_renderers=0):pass
            with self.assertRaises(ValueError):
                with capture_slots(p,{},coexistence=True):pass


if __name__=='__main__':unittest.main()
