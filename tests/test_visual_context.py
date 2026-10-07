import base64
import copy
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from loop_controller.core import Halt
from loop_controller.visual_context import TARGETS,contract,verify_payload,budget,visual_verdict
from loop_controller.model import image_part,conservative_prompt_bound


class VisualContextTests(unittest.TestCase):
    def inputs(self,d):
        paths=[]
        for name in [*TARGETS,'actual-before.png','actual-after.png']:
            p=Path(d)/name;p.write_bytes(b'\x89PNG\r\n\x1a\n'+name.encode());paths.append((name,p))
        return paths

    def messages(self,images):
        content=[]
        for label,path in images:content += [{'type':'text','text':label},image_part(path)]
        return [{'role':'user','content':content}]

    def test_broad_review_requires_all_five_targets_and_actual_pixels(self):
        with tempfile.TemporaryDirectory() as d:
            images=self.inputs(d);expected=contract(images,TARGETS,2,broad=True)
            receipt=verify_payload(self.messages(images),expected)
            self.assertTrue(receipt['verified']);self.assertEqual(receipt['image_count'],7)
            for missing in [images[1:],images[:5]]:
                with self.assertRaises(Halt):contract(missing,TARGETS,2,broad=True)

    def test_request_receipt_rejects_omitted_replaced_or_relabelled_pixels(self):
        with tempfile.TemporaryDirectory() as d:
            images=self.inputs(d);expected=contract(images,TARGETS,broad=True);messages=self.messages(images)
            for mode in ('omit','replace','relabel'):
                changed=copy.deepcopy(messages)
                if mode=='omit':changed[0]['content'].pop()
                if mode=='replace':changed[0]['content'][-1]=image_part(images[0][1])
                if mode=='relabel':changed[0]['content'][-2]['text']='reference pretending to be native'
                with self.subTest(mode=mode),self.assertRaises(Halt):verify_payload(changed,expected)

    def test_visual_budget_fits_seven_images_with_substantive_output(self):
        with tempfile.TemporaryDirectory() as d:
            config={};budget(config,broad=True)
            prompt=conservative_prompt_bound(self.messages(self.inputs(d)),[],lambda _:12000)
            self.assertLess(prompt+config['output_tokens'],config['working_context_tokens'])
            self.assertEqual(config['output_tokens'],16384)
            self.assertLess(config['working_context_tokens'],262144)

    def test_visual_pass_never_implies_final_game_acceptance(self):
        verdict=visual_verdict(dict(verdict='PASS',summary='Actual before/after improved.',fixes=[]))
        self.assertFalse(verdict['final_game_accepted']);self.assertFalse(verdict['gameplay_pass_is_visual_pass'])
        with self.assertRaises(ValueError):visual_verdict(dict(verdict='PASS',summary='',fixes=[]))


if __name__=='__main__':unittest.main()
