from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from author_character_plain_artifact import complete_source
from loop_controller.core import Halt,Store
from loop_controller.model import LocalModel


class PlainCharacterArtifactTests(unittest.TestCase):
    def response(self,content,finish='stop',**message):
        return dict(choices=[dict(finish_reason=finish,message=dict(role='assistant',content=content,**message))])

    def test_complete_public_file_only(self):
        self.assertEqual(complete_source(self.response('```python\nimport bpy\n```')),'import bpy\n')
        for value in [self.response('import bpy','length'),self.response('import bpy',tool_calls=[{}]),
                      self.response('<think>private</think>\nimport bpy'),self.response('import bpy\n'*241),
                      dict(error=dict(code='incomplete_tool_call'))]:
            with self.assertRaises(Halt):complete_source(value)
        with self.assertRaises(SyntaxError):complete_source(self.response('Here is code:\nimport bpy'))

    def test_plain_request_has_no_tool_exposure(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);store=Store(root/'run');model=object.__new__(LocalModel)
            model.store=store;model.guard=lambda:None;model.ready=lambda:None;model.text_counter=lambda s:len(s)//4
            model.config=dict(coordination_dir=str(root/'coord'),working_context_tokens=65536,
                output_tokens=1024,model_timeout_seconds=30)
            calls=[]
            def api(route,payload=None,timeout=10):
                calls.append(payload);return dict(self.response('import bpy'),usage=dict(prompt_tokens=50))
            model.api=api
            model.session('builder','plain','system','Return complete Python',[],{},turns=1,tool_choice='none')
            self.assertNotIn('tools',calls[0]);self.assertEqual(calls[0]['tool_choice'],'none')
            self.assertTrue(calls[0]['chat_template_kwargs']['enable_thinking'])
            self.assertEqual(calls[0]['reasoning_effort'],'xhigh')
            with self.assertRaises(ValueError):
                model.session('builder','invalid','system','prompt',[{}],{},tool_choice='none')


if __name__=='__main__':unittest.main()
