import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from watch_request_progress import stalled


class RequestProgressTests(unittest.TestCase):
    def test_elapsed_time_or_no_source_save_does_not_stop_progressing_request(self):
        old=dict(request_id='owned',generated_tokens=9600,last_activity_age_seconds=200,elapsed_seconds=5000)
        self.assertFalse(stalled(old,{**old,'generated_tokens':9601}))
        self.assertFalse(stalled(old,{**old,'last_activity_age_seconds':.1}))
        self.assertFalse(stalled(None,old))
        self.assertFalse(stalled(old,{**old,'request_id':'other'}))

    def test_two_matching_stale_counters_required(self):
        old=dict(request_id='owned',generated_tokens=9600,last_activity_age_seconds=181)
        self.assertTrue(stalled(old,{**old,'last_activity_age_seconds':201}))
        self.assertFalse(stalled({**old,'last_activity_age_seconds':170},old))
        self.assertFalse(stalled(old,{**old,'last_activity_age_seconds':None}))
        self.assertFalse(stalled({**old,'generated_tokens':0},{**old,'generated_tokens':0}))


if __name__=='__main__':unittest.main()
