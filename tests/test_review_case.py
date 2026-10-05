import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from loop_controller.core import Halt
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from resume_review_case import RESTORED_SOURCE,validate_case_pause,revalidate_review
from resume_failure_retry import ACCEPTED_COURIER


class ReviewCaseTests(unittest.TestCase):
    def test_only_saved_complete_lowercase_pass_is_revalidated(self):
        fields=dict(verdict='pass',summary='frame-002.png shows the failed state.',fixes=['Keep visual polish pending.'])
        value={'choices':[{'finish_reason':'tool_calls','message':{'tool_calls':[
            {'function':{'name':'submit_review','arguments':fields}}]}}]}
        original=copy.deepcopy(value)
        self.assertEqual(revalidate_review(value,['frame-002.png'])['verdict'],'PASS')
        self.assertEqual(value,original)
        for change in ['FIX','UNVERIFIED','nearly pass']:
            fields['verdict']=change
            with self.assertRaises((Halt,ValueError)):revalidate_review(value,['frame-002.png'])
        fields['verdict']='pass';value['choices'][0]['finish_reason']='length'
        with self.assertRaises(Halt):revalidate_review(value,['frame-002.png'])

    def test_stopped_history_is_required_and_not_reset(self):
        state=dict(task_index=3,source_checkpoint=RESTORED_SOURCE,last_playable_checkpoint=ACCEPTED_COURIER,
            task_failures=6,diagnosis_used=True,feedback={'bounded_stop':'context'},overall_deadline_epoch=HARD_CAP_EPOCH,
            blocker='Halt: Repeated diagnosed blocker on mission-failure-retry; failed source preserved and last playable state restored')
        original=copy.deepcopy(state);validate_case_pause(state);self.assertEqual(state,original)
        for changes in [dict(task_failures=0),dict(feedback={'verdict':'FIX'}),dict(source_checkpoint='other'),
                        dict(last_playable_checkpoint='other'),dict(overall_deadline_epoch=HARD_CAP_EPOCH+1)]:
            with self.subTest(changes=changes),self.assertRaises(Halt):validate_case_pause({**state,**changes})


if __name__=='__main__':unittest.main()
