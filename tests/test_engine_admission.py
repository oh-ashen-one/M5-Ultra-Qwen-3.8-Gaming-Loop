import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from engine_admission import ownership


class EngineAdmissionTests(unittest.TestCase):
    def test_native_player_is_counted_alongside_editor_and_blender(self):
        from unity_smoke import renderer_process
        self.assertTrue(renderer_process('/tmp/ChicagoLocalSlice.app/Contents/MacOS/Chicago Local Slice',
            'chicago local slice',['-force-metal']))
        self.assertFalse(renderer_process('/Applications/Unity.app/Contents/MacOS/Unity','unity',
            ['-nographics','-parentPid','11','-name','AssetImportWorkerHW0']))

    def setUp(self):
        self.blender=dict(pid=3,ppid=1,start=10,pgid=3,renderer=True)
        self.owner=dict(pid=10,ppid=1,start=20,pgid=10,renderer=False)
        self.editor=dict(pid=11,ppid=10,start=21,pgid=11,renderer=True)
        self.lease=dict(controller_pid=10,controller_start=20,engine_pid=11,engine_start=21)

    def test_owned_engine_and_preserved_external_renderer_fit_two_slots(self):
        d=ownership([self.blender,self.owner,self.editor],[self.blender],self.lease)
        self.assertEqual(d['status'],'available');self.assertEqual(d['owned_renderer_pids'],[11])

    def test_registered_group_remains_owned_after_editor_parent_exits(self):
        orphan=dict(pid=12,ppid=1,start=22,pgid=11,renderer=True)
        self.assertEqual(ownership([self.blender,self.owner,orphan],[self.blender],self.lease)['status'],'available')

    def test_real_third_renderer_is_a_capacity_wait_even_if_owned(self):
        worker=dict(pid=12,ppid=11,start=22,pgid=11,renderer=True)
        d=ownership([self.blender,self.owner,self.editor,worker],[self.blender],self.lease)
        self.assertEqual(d['status'],'capacity-wait');self.assertIn('renderer-capacity',d['reasons'])

    def test_null_worker_consumes_no_render_slot(self):
        worker=dict(pid=12,ppid=11,start=22,pgid=11,renderer=False,null_import_worker=True)
        self.assertEqual(ownership([self.blender,self.owner,self.editor,worker],[self.blender],self.lease)['status'],'available')

    def test_foreign_job_and_reused_pid_are_not_claimed(self):
        other=dict(pid=12,ppid=1,start=22,pgid=12,renderer=True)
        d=ownership([self.blender,self.owner,other],[self.blender],self.lease)
        self.assertEqual(d['foreign_renderer_pids'],[12])
        reused={**self.blender,'start':100}
        self.assertEqual(ownership([reused],[self.blender])['status'],'capacity-wait')

    def test_reused_controller_identity_cannot_own_engine_group(self):
        d=ownership([self.blender,{**self.owner,'start':99},self.editor],[self.blender],self.lease)
        self.assertIn('lease-owner-missing-or-reused',d['reasons'])
        self.assertEqual(d['foreign_renderer_pids'],[11])

    def test_group_members_predating_lease_are_not_owned(self):
        wrong={**self.editor,'start':19,'ppid':1}
        self.assertEqual(ownership([self.blender,self.owner,wrong],[self.blender],self.lease)['foreign_renderer_pids'],[11])


if __name__=='__main__':unittest.main()
