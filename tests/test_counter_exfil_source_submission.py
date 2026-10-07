from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from submit_counter_exfil_parts import writes_shared_signals,final_source_parameter

class SharedSignalBoundaryTests(unittest.TestCase):
    def test_recovers_only_complete_final_source_separate_from_reasoning(self):
        source='using UnityEngine;\nclass CounterExfilRunner {}\n'
        message=dict(content='<parameter name="content">'+source+'</parameter>',reasoning_content='private')
        response=dict(choices=[dict(finish_reason='stop',message=message)])
        self.assertEqual(final_source_parameter(response),source)
        for replacement in (dict(message,content=message['content']+' extra'),
                dict(message,content=message['content'][:-12]),dict(message,reasoning_content=None),
                dict(message,tool_calls=[{'id':'already-handled'}]),dict(message,content='Saved the file')):
            with self.assertRaises(ValueError):final_source_parameter(dict(choices=[dict(finish_reason='stop',message=replacement)]))
        with self.assertRaises(ValueError):final_source_parameter(dict(choices=[dict(finish_reason='length',message=message)]))
    def test_read_comparisons_are_allowed_but_shared_state_writes_are_not(self):
        for source in ('LoopSignals.Mode == "foot"','LoopSignals.Health <= 0','LoopSignals.Restarts != old'):
            self.assertFalse(writes_shared_signals(source))
        for source in ('LoopSignals.Health = 100','LoopSignals.Health += 10','LoopSignals.Restarts++','LoopSignals.Shots--'):
            self.assertTrue(writes_shared_signals(source))

if __name__=='__main__':unittest.main()
