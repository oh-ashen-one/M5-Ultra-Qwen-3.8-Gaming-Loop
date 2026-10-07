import ast
import datetime
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from qwen_capacity import assess,CompressionWatch,GIB,MIB


class CapacityTests(unittest.TestCase):
    def sample(self,available=63.811,unreal=30.675,qwen=139.7,**extra):
        return dict(available_bytes=available*GIB,unreal_bytes=unreal*GIB,qwen_bytes=qwen*GIB,
            swap_bytes=44*MIB,compressed_bytes=2*GIB,pressure_level=1,**extra)

    def base(self):return dict(swap_bytes=43.1875*MIB,compressed_bytes=1.9*GIB)

    def test_measured_overlap_is_admitted_without_double_reserving_unreal(self):
        value=assess(self.sample(),self.base())
        self.assertTrue(value['passed']);self.assertAlmostEqual(value['required_available_gib'],41.325)
        self.assertAlmostEqual(value['swap_growth_mib'],.8125)

    def test_reserve_tracks_future_unreal_growth(self):
        absent=assess(self.sample(available=96,unreal=0),self.base())
        grown=assess(self.sample(available=66,unreal=30),self.base())
        self.assertEqual(absent['required_available_gib'],72)
        self.assertEqual(grown['required_available_gib'],42)
        self.assertEqual(absent['available_gib']-absent['required_available_gib'],
                         grown['available_gib']-grown['required_available_gib'])

    def test_load_peak_is_budgeted_as_remaining_allocation(self):
        self.assertFalse(assess(self.sample(available=219,unreal=0,qwen=0),self.base(),'load')['passed'])
        self.assertTrue(assess(self.sample(available=230,unreal=0,qwen=0),self.base(),'load')['passed'])
        progressing=assess(self.sample(available=130,unreal=0,qwen=100),self.base(),'load')
        self.assertTrue(progressing['passed']);self.assertEqual(progressing['remaining_model_load_gib'],48)

    def test_real_pressure_guards_and_trial_envelope_fail_closed(self):
        cases=[('available_bytes',35*GIB,'measured-capacity-budget'),
            ('unreal_bytes',41*GIB,'unreal-exceeds-measured-trial-envelope'),
            ('qwen_bytes',193*GIB,'qwen-footprint-above192GiB'),
            ('swap_bytes',600*MIB,'swap-growth-above512MiB'),
            ('pressure_level',2,'OS-memory-pressure'),('thermal_warning',2,'OS-thermal-warning')]
        for phase in ('load','settle','steady'):
            for key,value,reason in cases:
                sample=self.sample();sample[key]=value
                with self.subTest(phase=phase,key=key):self.assertIn(reason,assess(sample,self.base(),phase)['failure'])

    def test_real_trial_entrypoint_cannot_select_custom_or_disable_guard(self):
        source=(Path(__file__).resolve().parents[1]/'tools/flash_next_capacity_trial.py').read_text()
        tree=ast.parse(source)
        argv=next(n.value for n in ast.walk(tree) if isinstance(n,ast.Assign)
            and any(isinstance(t,ast.Name) and t.id=='argv' for t in n.targets))
        literals=[n.value for n in argv.elts if isinstance(n,ast.Constant)]
        self.assertIn('--memory-guard',literals);self.assertIn('safe',literals)
        self.assertNotIn('--memory-guard-gb',literals);self.assertNotIn('off',literals)

    def test_controller_default_floor_is_unchanged_and_trial_is_explicit(self):
        from loop_controller.adapters import Machine
        from loop_controller.core import Halt
        with tempfile.TemporaryDirectory() as directory:
            machine=Machine.__new__(Machine);machine.child=None;machine.baseline_swap=0
            machine.c=dict(coordination_dir=directory,wall_hours=24,minimum_disk_GiB=0,
                authorized_shared_coexistence=True)
            machine.store=SimpleNamespace(root=Path(directory),get=lambda k,d=None:d,set=lambda **kw:None)
            fake=SimpleNamespace(virtual_memory=lambda:SimpleNamespace(available=63*GIB),
                swap_memory=lambda:SimpleNamespace(used=0))
            with patch('loop_controller.adapters.psutil',fake), \
                    patch('loop_controller.adapters.subprocess.check_output',return_value='fixture-user'), \
                    patch('engine_admission.hardware_pressure',return_value={'thermal_warning':0}):
                with self.assertRaises(Halt):machine.guard()
                machine.capacity_budget=SimpleNamespace(observe=lambda **kw:dict(passed=True,failure=[]))
                machine.guard()

    def test_simultaneous_migration_preserves_stopped_source_and_one_attempt(self):
        from qualify_qwen_capacity import validate_boundary, CapacityAuthor, SOURCE, ACCEPTED, HARD_CAP_EPOCH
        from loop_controller.core import Halt
        old=dict(status='paused',controller_pid=None,owned_process=None,current_round='q0144-dd98c86e',
            source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,task_index=7,task_failures=24,
            failure_streak=1,diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,
            shared_workload_priority='simultaneous-no-default-priority',capacity_trial_runtime_attempted=True,
            blocker='Halt: Capacity trial stopped during model load: compressor-growth-above2GiB; no author request started',
            capacity_trial_load_outcome=dict(policy='simultaneous-capacity-trial-v1',candidate=SOURCE,
                cause='compressor-growth-above2GiB',author_requests=0,all_owned_processes_stopped=True),
            player_death_focused_fault={'cause':'resident available-memory guard'})
        validate_boundary(old)
        settings=CapacityAuthor.__new__(CapacityAuthor).recovery_settings()
        self.assertEqual(settings['shared_workload_priority'],'simultaneous-no-default-priority')
        self.assertNotIn('capacity_trial_phase_recovery_attempted',old)
        for changed in ({'capacity_trial_author_attempted':True},{'source_checkpoint':'different'},
                {'controller_pid':123},{'task_failures':0},{'overall_deadline_epoch':HARD_CAP_EPOCH+3600}):
            with self.subTest(changed=changed),self.assertRaises(Halt):validate_boundary(dict(old,**changed))

    def test_recorded_load_spike_is_telemetry_not_a_standalone_fault(self):
        rows=json.loads((Path(__file__).resolve().parents[1]/'diagnostics/capacity-2026-10-07/load-stop.json').read_text())['trial_samples']
        watch=CompressionWatch();start=datetime.datetime.fromisoformat(rows[0]['utc']).timestamp()
        for row in rows:
            sample=self.sample(available=row['available_gib'],unreal=row['unreal_footprint_gib'],qwen=row['qwen_footprint_gib'])
            sample.update(compressed_bytes=self.base()['compressed_bytes']+row['compression_growth_gib']*GIB,
                swap_bytes=self.base()['swap_bytes']+row['swap_growth_mib']*MIB)
            budget=assess(sample,self.base(),'load')
            self.assertTrue(budget['passed'])
            self.assertFalse(watch.observe(sample,budget,datetime.datetime.fromisoformat(row['utc']).timestamp()-start)['failure'])
        self.assertGreater(budget['compression_growth_gib'],11)

    def test_sustained_growth_with_swap_activity_stops_in_each_phase(self):
        for phase in ('load','settle','steady'):
            watch=CompressionWatch();observations=[]
            for t in range(0,46,5):
                sample=self.sample();sample.update(compressed_bytes=(2+t*.12)*GIB,swapout_bytes=t*4*MIB)
                observations.append(watch.observe(sample,dict(phase=phase,available_gib=116,required_available_gib=84),t))
            with self.subTest(phase=phase):
                self.assertFalse(observations[6]['failure']);self.assertTrue(observations[8]['failure'])

    def test_repeated_compression_decompression_with_low_margin_stops(self):
        watch=CompressionWatch()
        for t in range(0,46,5):
            sample=self.sample();sample.update(compression_bytes=t*.15*GIB,decompression_bytes=t*.15*GIB)
            result=watch.observe(sample,dict(phase='steady',available_gib=88,required_available_gib=84),t)
        self.assertTrue(result['failure']);self.assertEqual(result['window_growth_gib'],0)

    def test_stable_loaded_compression_and_short_stress_do_not_stop(self):
        watch=CompressionWatch()
        for t in range(0,91,5):
            phase='load' if t<20 else 'settle' if t<50 else 'steady'
            sample=self.sample();sample.update(compressed_bytes=(2 if t<15 else 13)*GIB)
            result=watch.observe(sample,dict(phase=phase,available_gib=116,required_available_gib=84),t)
            self.assertFalse(result['failure'])
        self.assertEqual(result['phase_growth_gib'],0)
        watch=CompressionWatch()
        for t in range(0,46,5):
            sample=self.sample();sample.update(compressed_bytes=(2+t*.12)*GIB)
            result=watch.observe(sample,dict(phase='steady',available_gib=88 if t<=30 else 116,required_available_gib=84),t)
            self.assertFalse(result['failure'])

    def test_phase_change_does_not_erase_stress_but_sampling_gap_does(self):
        watch=CompressionWatch()
        for t in range(0,36,5):
            sample=self.sample();sample.update(compressed_bytes=(2+t*.12)*GIB,swapout_bytes=t*4*MIB)
            watch.observe(sample,dict(phase='load' if t<35 else 'settle',available_gib=116,required_available_gib=84),t)
        sample.update(compressed_bytes=7*GIB,swapout_bytes=160*MIB)
        self.assertTrue(watch.observe(sample,dict(phase='settle',available_gib=116,required_available_gib=84),40)['failure'])
        self.assertFalse(watch.observe(sample,dict(phase='steady',available_gib=116,required_available_gib=84),60)['failure'])


if __name__=='__main__':unittest.main()
