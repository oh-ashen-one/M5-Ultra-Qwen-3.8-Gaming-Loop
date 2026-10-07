import copy
import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from resume_hud_bounded_review import focused_facts, SOURCE
from loop_controller.core import Halt
from loop_controller.model import conservative_prompt_bound


class HudBoundedReviewTests(unittest.TestCase):
    def gate(self):
        return dict(passed=True, candidate_commit=SOURCE, build_id='native-build',
            consolidated_hud={'passed': True},
            regressions={'regressions': [dict(test=str(i), gate=dict(passed=True, candidate_commit=SOURCE)) for i in range(10)]},
            hud_regressions=[dict(check={'passed': True, 'samples': ['large diagnostic'] * 1000}) for _ in range(10)])

    def test_compaction_preserves_all_pass_requirements(self):
        for mutation in ('native', 'source', 'missing', 'hud', 'regression-source'):
            g = self.gate()
            if mutation == 'native': g['passed'] = False
            if mutation == 'source': g['candidate_commit'] = 'other'
            if mutation == 'missing': g['regressions']['regressions'].pop()
            if mutation == 'hud': g['hud_regressions'][2]['check']['passed'] = False
            if mutation == 'regression-source': g['regressions']['regressions'][2]['gate']['candidate_commit'] = 'other'
            with self.subTest(mutation=mutation), self.assertRaises(Halt): focused_facts(g)

    def test_four_images_fit_without_changing_context_or_output_budget(self):
        g = self.gate(); before = copy.deepcopy(g)
        text = json.dumps(focused_facts(g))
        messages = [{'role': 'user', 'content': [{'type': 'text', 'text': text + 'x' * 4000}] +
                    [{'type': 'image_url', 'image_url': {'url': 'unchanged PNG'}}] * 4}]
        self.assertLess(conservative_prompt_bound(messages, []) + 8192, 65536)
        self.assertEqual(g, before)


if __name__ == '__main__': unittest.main()
