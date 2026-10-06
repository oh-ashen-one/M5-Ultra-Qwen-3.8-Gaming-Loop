import math
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from resume_map_support import compose_clear_walk, ground_span, validate_support_pause, SOURCE, ROUND, ACCEPTED
from loop_controller.core import Halt
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.recovery_policy import support_repair_scope
from unittest.mock import patch


class MapSupportTests(unittest.TestCase):
    def test_scope_uses_failure_time_not_last_driving_endpoint(self):
        surface={'min':[-1,0,-2], 'max':[22,.14,30]}
        gate={'failure':['vehicle-rendered-support','rendered-pavement-support'],
              'scoped_facts':{'rendered_walking_support':{'surfaces':[surface],
                  'first_uncovered':[{'time':8.15,'player':[4,.695,11]}]}}}
        rows=[{'time':21.3,'mode':'vehicle','vehicle':[3.36,1.378,7.96]},
              {'time':34,'mode':'vehicle','vehicle':[4,.14,17]}]
        self.assertEqual(support_repair_scope(gate,rows,22.6),['walking-prefix','vehicle-source'])
        rows[0]['time']=23
        self.assertEqual(support_repair_scope(gate,rows,22.6),['walking-prefix'])
        gate['scoped_facts']['rendered_walking_support']['first_uncovered'][0]['time']=23
        self.assertEqual(support_repair_scope(gate,rows,22.6),[])

    def test_clear_walk_keeps_no_reset_and_has_released_outside_dwell(self):
        fields=dict(north_seconds=4.78125,east_seconds=3.91666,west_seconds=3.29166,
                    south_seconds=2.8125,summary='Cross at Z17 to avoid the observed pier-base walking support failure.')
        p=compose_clear_walk(fields)['scenario']; steps=p['steps']
        self.assertEqual([s['keys'] for s in steps],[['W'],['D'],['A'],['S'],['E']])
        self.assertAlmostEqual(steps[2]['start']-steps[1]['end'],1.2)
        self.assertEqual(steps[0]['start'],4)
        self.assertEqual(len(p['captures']),5)
        fields['north_seconds']=math.nan
        with self.assertRaises(ValueError):compose_clear_walk(fields)

    def test_ground_span_excludes_exit_and_includes_closing_braces(self):
        raw='before\n// Ground snap: raycast down skipping own collider\nif (a) {\nif (b) {\nx();\n}\n}\n\nif (e) Exit();\nafter\n'
        first,last=ground_span(raw)
        selected='\n'.join(raw.splitlines()[first-1:last])
        self.assertEqual(selected.count('}'),2)
        self.assertNotIn('Exit',selected)
        with self.assertRaises(Halt):ground_span(raw+raw)

    def test_exact_pause_rejects_changed_counters(self):
        state=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=ROUND,
            task_index=7,task_failures=13,failure_streak=2,diagnosis_used=True,
            overall_deadline_epoch=HARD_CAP_EPOCH,blocker='Halt: Explicit controller stop',
            map_drive_exact_attempted=True,map_traversal_strategies=[
                {'round':'q0063-6b7c8ebe'},{'round':'q0064-fefd3c3e'}])
        validate_support_pause(state)
        state['task_failures']=0
        with self.assertRaises(Halt):validate_support_pause(state)

    def test_compiler_repair_preserves_exhausted_route_history(self):
        import resume_map_support_compile as c
        state=dict(source_checkpoint=c.SOURCE,last_playable_checkpoint=c.ACCEPTED,current_round=c.ROUND,
            task_index=7,task_failures=14,failure_streak=1,diagnosis_used=True,
            overall_deadline_epoch=HARD_CAP_EPOCH,map_support_repair_attempted=True,
            blocker='Halt: Repeated diagnosed blocker on connected-map-extension; failed source preserved and last playable state restored',
            map_traversal_strategies=[{}, {}, {'round':c.ROUND}],last_valid_replay={})
        with patch.object(c,'replay_identity',return_value=c.REPLAY):
            c.validate_compile_pause(state)
            state['map_traversal_strategies'].pop(0)
            with self.assertRaises(Halt):c.validate_compile_pause(state)
