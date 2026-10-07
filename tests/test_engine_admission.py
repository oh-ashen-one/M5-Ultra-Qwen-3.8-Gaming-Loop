import sys
from pathlib import Path
import unittest
from types import SimpleNamespace
from unittest.mock import Mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from engine_admission import ownership, complete_process_scan,resource_reasons,thermal_warning


class EngineAdmissionTests(unittest.TestCase):
    def test_partial_process_inventory_is_discarded_before_retry(self):
        def broken():
            yield 'partial-old-entry'
            raise SystemError('<built-in function proc_cmdline> returned a result with an exception set')
        module = SimpleNamespace(process_iter=Mock(side_effect=[broken(), iter(['complete-renderer', 'complete-owner'])]))
        with self.assertWarns(RuntimeWarning):
            self.assertEqual(complete_process_scan(['cmdline'], module), ['complete-renderer', 'complete-owner'])
        self.assertEqual(module.process_iter.call_count, 2)

    def test_repeated_or_unrelated_scan_failure_still_stops_admission(self):
        for errors, calls in [([SystemError('proc_cmdline failed')] * 2, 2),
                              ([SystemError('unrelated native failure')], 1)]:
            module = SimpleNamespace(process_iter=Mock(side_effect=errors))
            with self.assertRaises(SystemError):
                if calls == 2:
                    with self.assertWarns(RuntimeWarning): complete_process_scan(['cmdline'], module)
                else: complete_process_scan(['cmdline'], module)
            self.assertEqual(module.process_iter.call_count, calls)

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

    def test_authorized_idle_blender_and_unreal_do_not_veto_qwen(self):
        unreal=dict(pid=40,ppid=1,start=25,pgid=40,renderer=True)
        rows=[self.blender,unreal,self.owner,self.editor]
        result=ownership(rows,[self.blender],self.lease,coexistence=True)
        self.assertEqual(result['status'],'available')
        self.assertEqual(result['owned_renderer_pids'],[11]);self.assertEqual(result['foreign_renderer_pids'],[40])
        self.assertEqual(resource_reasons(149.94,0,0),[])
        self.assertEqual(ownership([self.blender,unreal],[self.blender],coexistence=True)['status'],'available')

    def test_actual_memory_swap_and_thermal_pressure_still_block(self):
        for available,swap,thermal in [(63,0,0),(150,513,0),(150,0,1),(150,0,3)]:
            with self.subTest(available=available,swap=swap,thermal=thermal):
                self.assertTrue(resource_reasons(available,swap,thermal))
        self.assertEqual(thermal_warning('Note: No thermal warning level has been recorded'),0)
        self.assertEqual(thermal_warning('Thermal_Level = 2'),2)
        self.assertEqual(thermal_warning('ThermalPressure: critical'),3)

    def test_coexistence_never_adopts_foreign_work_or_waives_owned_engine_bounds(self):
        invalid={**self.owner,'start':99}
        result=ownership([self.blender,invalid,self.editor],[self.blender],self.lease,coexistence=True)
        self.assertIn('lease-owner-missing-or-reused',result['reasons'])
        self.assertEqual(result['owned_renderer_pids'],[])
        worker=dict(pid=12,ppid=11,start=22,pgid=11,renderer=True)
        result=ownership([self.blender,self.owner,self.editor,worker],[self.blender],self.lease,coexistence=True)
        self.assertIn('multiple-owned-renderers',result['reasons'])


if __name__=='__main__':unittest.main()
