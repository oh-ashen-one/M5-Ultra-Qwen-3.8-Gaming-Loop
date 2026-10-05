from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from inspect_combat_contracts import summarize_combat


class CombatObservationTests(unittest.TestCase):
    def test_damage_and_pursuit_use_actual_vehicle_distance_in_diagnostic(self):
        rows=[]
        for t,hp in [(10,100),(12,96)]:
            rows.append(dict(time=t,mode='vehicle',health=hp,pursuit=3,restarts=0,
                rivals=[dict(alive=True,actorDistance=23,footDistance=3,attackUnobstructed=False,firstAttackCollider='wall')]))
        facts=summarize_combat(rows)
        self.assertEqual(facts['pursuit_while_vehicle_over_18m'],[3])
        self.assertEqual(facts['damage_events'][0]['actor_distance'],23)
        self.assertFalse(facts['damage_events'][0]['unobstructed'])
        self.assertFalse(facts['gameplay_acceptance_claimed'])


if __name__=='__main__':unittest.main()
