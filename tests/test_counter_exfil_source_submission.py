from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from submit_counter_exfil_parts import writes_shared_signals

class SharedSignalBoundaryTests(unittest.TestCase):
    def test_read_comparisons_are_allowed_but_shared_state_writes_are_not(self):
        for source in ('LoopSignals.Mode == "foot"','LoopSignals.Health <= 0','LoopSignals.Restarts != old'):
            self.assertFalse(writes_shared_signals(source))
        for source in ('LoopSignals.Health = 100','LoopSignals.Health += 10','LoopSignals.Restarts++','LoopSignals.Shots--'):
            self.assertTrue(writes_shared_signals(source))

if __name__=='__main__':unittest.main()
