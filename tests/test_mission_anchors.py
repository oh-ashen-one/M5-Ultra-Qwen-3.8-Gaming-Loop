"""Red cases for objectives inheriting player motion despite a claimed mission completion."""
import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from loop_controller.mission_anchors import inspect_mission_anchors


class MissionAnchorTests(unittest.TestCase):
    def rows(self):
        rows = []
        for time, player, carried, keys, mode, mission in [
            (3, [0, 0, 0], False, [], 'foot', 'active'),
            (5, [0, 0, -2], False, ['S'], 'foot', 'active'),
            (6, [0, 0, 1], False, ['W'], 'foot', 'active'),
            (7, [0, 0, 1], True, ['F'], 'foot', 'active'),
            (8, [0, 0, 8], True, ['W'], 'vehicle', 'active'),
            (9, [0, 0, 10], True, ['F'], 'vehicle', 'complete'),
        ]:
            objects = [{'name':'Parcel','position':player if carried else [0, .5, 2], 'playerChild':carried},
                       {'name':'DropPad','position':[0, 0, 10], 'playerChild':False},
                       {'name':'Beacon','position':[0, 3, 10], 'playerChild':False}]
            rows.append(dict(time=time, player=player, vehicle=player, keys=keys, mode=mode,
                             mission=mission, missionObjects=objects))
        return rows

    def test_actual_pickup_can_carry_parcel_but_world_markers_must_stay_fixed(self):
        rows = self.rows()
        self.assertTrue(inspect_mission_anchors(rows)['passed'])
        rows[2]['missionObjects'][1]['position'][2] += 1
        self.assertIn('DropPad-world-anchor-moved', inspect_mission_anchors(rows)['failure'])

    def test_player_children_cannot_pass_even_with_constant_reported_world_positions(self):
        rows = self.rows()
        for row in rows:
            for obj in row['missionObjects']: obj['playerChild'] = True
        self.assertFalse(inspect_mission_anchors(rows)['passed'])

    def test_claimed_completion_without_return_input_or_destination_is_rejected(self):
        rows = self.rows()
        for mutate in ('return', 'pickup', 'delivery', 'destination', 'observations'):
            with self.subTest(mutate=mutate):
                changed = copy.deepcopy(rows)
                if mutate == 'return': changed[2]['player'] = [0, 0, -2]
                if mutate == 'pickup': changed[3]['keys'] = []
                if mutate == 'delivery': changed[-1]['keys'] = []
                if mutate == 'destination': changed[-1]['vehicle'] = [0, 0, 3]
                if mutate == 'observations':
                    for row in changed: row.pop('missionObjects')
                self.assertFalse(inspect_mission_anchors(changed)['passed'])


if __name__ == '__main__': unittest.main()
