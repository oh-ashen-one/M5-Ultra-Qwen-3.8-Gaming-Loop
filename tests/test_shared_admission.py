import contextlib
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from loop_controller.shared_admission import admitted
from loop_controller.core import Halt, Store, atomic, read_json


class SharedAdmissionTests(unittest.TestCase):
    def setup_store(self, d):
        store=Store(d); self.addCleanup(store.db.close)
        store.set(stage='native-test', task_failures=24, controller_pid=42)
        request=Path(d)/'request.json'; lease=dict(lease_id='owned',expires_epoch=200)
        atomic(request,lease)
        return store,request,lease

    def test_waiter_keeps_resident_yielded_then_launches_once(self):
        with tempfile.TemporaryDirectory() as d:
            store,request,lease=self.setup_store(d); calls=[]; sleeps=[]; exited=[]
            @contextlib.contextmanager
            def factory():
                calls.append(True)
                if len(calls)==1: raise RuntimeError('Existing shared GPU waiters have priority')
                try: yield
                finally: exited.append(True)
            def sleep(seconds):
                self.assertTrue(request.exists()); self.assertEqual(store.get('status'),'capacity-wait')
                self.assertEqual(store.get('controller_pid'),42); sleeps.append(seconds)
            with admitted(factory,lambda:None,store,request,lease,900,sleeper=sleep,clock=lambda:1000):
                self.assertEqual(len(calls),2); self.assertEqual(store.get('status'),'running')
                self.assertEqual(read_json(request)['expires_epoch'],1990)
                self.assertEqual(store.get('task_failures'),24)
            self.assertEqual(sleeps,[30]); self.assertEqual(exited,[True])

    def test_fault_in_engine_body_is_never_interpreted_as_admission_retry(self):
        with tempfile.TemporaryDirectory() as d:
            store,request,lease=self.setup_store(d); calls=[]
            @contextlib.contextmanager
            def factory(): calls.append(True); yield
            with self.assertRaises(RuntimeError):
                with admitted(factory,lambda:None,store,request,lease,90):
                    raise RuntimeError('Existing shared GPU waiters have priority')
            self.assertEqual(len(calls),1)

    def test_access_errors_resource_guards_and_lease_changes_are_preserved(self):
        for kind in ['access','resource','lease']:
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as d:
                store,request,lease=self.setup_store(d); calls=[]
                @contextlib.contextmanager
                def factory():
                    calls.append(True)
                    raise RuntimeError('Permission denied')
                    yield
                def guard():
                    if kind=='resource': raise Halt('Memory/swap bound exceeded')
                if kind=='lease': atomic(request,dict(lease_id='other'))
                with self.assertRaises((Halt,RuntimeError)):
                    with admitted(factory,guard,store,request,lease,90): self.fail('Must not launch')
                self.assertEqual(len(calls),1 if kind=='access' else 0)

    def test_continuous_wait_is_bounded_and_does_not_launch(self):
        with tempfile.TemporaryDirectory() as d:
            store,request,lease=self.setup_store(d); elapsed=[0]
            @contextlib.contextmanager
            def factory():
                raise RuntimeError('Existing GPU holder requires coordination')
                yield
            with self.assertRaisesRegex(Halt,'within300seconds'):
                with admitted(factory,lambda:None,store,request,lease,900,
                    sleeper=lambda n:elapsed.__setitem__(0,elapsed[0]+n),monotonic=lambda:elapsed[0]):
                    self.fail('No engine permitted')
            self.assertEqual(elapsed[0],300); self.assertTrue(request.exists())


if __name__ == '__main__': unittest.main()
