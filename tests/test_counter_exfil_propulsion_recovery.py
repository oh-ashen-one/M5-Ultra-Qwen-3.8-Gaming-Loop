from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from recover_counter_exfil_propulsion import final_fields

class ExactFinalRecoveryTests(unittest.TestCase):
    def response(self,content,finish='stop',**extra):
        return dict(choices=[dict(finish_reason=finish,message=dict(content=content,reasoning_content='private',**extra))])
    def test_only_complete_final_fields_are_recovered(self):
        content='<invoke name="finish_source"><parameter name="runner_source">R</parameter><parameter name="spawn_method">S</parameter><parameter name="hint_property">H</parameter></invoke>'
        self.assertEqual(final_fields(self.response(content)),dict(runner_source='R',spawn_method='S',hint_property='H'))
        for bad in [self.response(content+' extra'),self.response(content[:-9]),self.response(content,'length'),self.response('saved'),self.response(content,tool_calls=[{}])]:
            with self.assertRaises(ValueError):final_fields(bad)

if __name__=='__main__':unittest.main()
