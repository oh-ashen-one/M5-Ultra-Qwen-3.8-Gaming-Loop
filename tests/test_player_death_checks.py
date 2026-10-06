import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from loop_controller.player_death_checks import CASES, death_probe, inspect_player_death


class PlayerDeathChecks(unittest.TestCase):
    def evidence(self):
        case = 'courier-delivery'; at = CASES[case][0]; reset = at + 3.5
        before = dict(courierStage=1, carrying=True, routeStage=0, routeComplete=False,
            relayActive=False, relayComplete=False, relayFailed=False, relayCount=0,
            interceptionActive=False, interceptionComplete=False, interceptionFailed=False,
            stopped=0, spawned=0, escaped=0)
        injection = dict(caseName=case, healthBefore=80, healthAfter=0, restarts=0,
            time=at+.03, keys=['F'], shots=4, mode='vehicle', before=before)
        rows = []
        for i in range(29):
            rows.append(dict(time=at+.25+i*.1, health=0, shots=4, restarts=0, mode='vehicle',
                player=[0,0,0], vehicle=[3,0,8], playerDeath=copy.deepcopy(before),
                routeChapter={'hudPanels':[{'name':'MissionBoard','visible':True,'text':'HEALTH DEPLETED\nR reset'}]}))
        clean = dict(before, courierStage=0, carrying=False)
        for i in range(7):
            rows.append(dict(time=reset+.45+i*.1, health=100, shots=0, hits=0, restarts=1,
                mode='foot', mission='active', player=[0,.14,1.7], playerDeath=copy.deepcopy(clean)))
        rows.append(dict(time=reset+3, restarts=1, player=[0,.14,4.9]))
        return case, rows, injection

    def test_complete_gated_death_and_real_reset_contract(self):
        case, rows, injection = self.evidence()
        self.assertTrue(inspect_player_death(rows, injection, case)['passed'])

    def test_simultaneous_completion_is_not_hidden_by_later_failed_hud(self):
        case, rows, injection = self.evidence()
        rows[0]['playerDeath']['courierStage'] = 2
        result = inspect_player_death(rows, injection, case)
        self.assertIn('objective-progression-after-zero-health', result['failure'])

    def test_firing_and_movement_fail_even_with_failed_hud(self):
        case, rows, injection = self.evidence()
        rows[2]['shots'] = 5; rows[3]['vehicle'][0] += 1
        result = inspect_player_death(rows, injection, case)
        self.assertIn('player-can-fire-while-dead', result['failure'])
        self.assertIn('vehicle-moves-under-dead-input', result['failure'])

    def test_invalid_chapter_and_reset_cannot_pass(self):
        case, rows, injection = self.evidence()
        injection['before']['courierStage'] = 0
        for row in rows:
            if row.get('restarts') == 1 and 'health' in row: row['health'] = 0
        result = inspect_player_death(rows, injection, case)
        self.assertFalse(result['setup_passed'])
        self.assertIn('whole-reset-state-not-restored', result['failure'])

    def test_probe_keeps_prefix_and_uses_only_declared_negative_intervention(self):
        original = {'steps':[dict(start=4,end=5,keys=['W']),dict(start=14.3,end=14.6,keys=['F']),
                             dict(start=16,end=17,keys=['S'])]}
        probe = death_probe(original, 'courier-delivery')
        self.assertEqual(probe['steps'][0], original['steps'][0])
        self.assertEqual(probe['death_key'], 'F')
        self.assertNotIn(original['steps'][2], probe['steps'])
        self.assertTrue(any('R' in step['keys'] for step in probe['steps']))

    def test_unity_float32_boundary_is_valid_but_earlier_frame_is_not(self):
        injection = dict(caseName='relay-final', healthBefore=44, healthAfter=0, restarts=0,
            time=59.599998474121094, keys=['F'], before={'routeStage':2,'relayCount':2,'relayComplete':False})
        self.assertTrue(inspect_player_death([], injection, 'relay-final')['setup_passed'])
        injection['time'] = 59.58
        self.assertFalse(inspect_player_death([], injection, 'relay-final')['setup_passed'])
        injection['time'] = 59.599998474121094; injection['keys'] = []
        self.assertFalse(inspect_player_death([], injection, 'relay-final')['setup_passed'])


if __name__ == '__main__': unittest.main()
