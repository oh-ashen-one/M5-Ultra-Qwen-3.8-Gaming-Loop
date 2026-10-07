import ast
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from qwen_capacity import assess,GIB,MIB


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
            ('compressed_bytes',4*GIB,'compressor-growth-above2GiB'),
            ('pressure_level',2,'OS-memory-pressure'),('thermal_warning',2,'OS-thermal-warning')]
        for key,value,reason in cases:
            sample=self.sample();sample[key]=value
            with self.subTest(key=key):self.assertIn(reason,assess(sample,self.base())['failure'])

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


if __name__=='__main__':unittest.main()
