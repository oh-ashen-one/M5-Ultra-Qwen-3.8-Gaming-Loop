import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from resume_post_relay_design import PostRelayDesign,TASK,validate_pause,SOURCE,ROUND,ACCEPTED
from loop_controller.core import Halt
from loop_controller.delivery_policy import HARD_CAP_EPOCH

class PostRelayDesignTests(unittest.TestCase):
    def test_actual_begin_contract_has_complete_task_metadata(self):
        state={'rounds':111}
        store=SimpleNamespace(get=lambda k,d=None:state.get(k,d),set=lambda **kw:state.update(kw),report=lambda:None)
        runner=SimpleNamespace(store=store,machine=SimpleNamespace(guard=lambda:None))
        ident=PostRelayDesign.begin(runner,TASK,'local-next-playable-increment')
        self.assertTrue(ident.startswith('q0112-'))
        self.assertEqual(state['current_task'],TASK['outcome'])

    def test_only_exact_pre_inference_metadata_fault_is_recoverable(self):
        state=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=ROUND,
            task_index=7,task_failures=24,failure_streak=1,diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,
            blocker="KeyError: 'outcome'",post_relay_design_attempted=True,relay_outcome={'accepted':True})
        validate_pause(state)
        for change in [{'blocker':'other'},{'post_relay_metadata_repaired':True},{'post_relay_plan':{'ok':True}},
                       {'source_checkpoint':'different'},{'task_failures':0}]:
            with self.subTest(change=change),self.assertRaises(Halt):validate_pause({**state,**change})

if __name__=='__main__':unittest.main()
