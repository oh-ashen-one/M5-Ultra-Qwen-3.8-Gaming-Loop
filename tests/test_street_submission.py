import copy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import resume_street_submission as recovery
from resume_saved_door import STREET_PATHS
from loop_controller.core import Halt, sha
from loop_controller.model import tool, typed_arguments


class StreetSubmissionTests(unittest.TestCase):
    def test_exact_source_only_stop_retains_rejection_history(self):
        state=dict(source_checkpoint=recovery.SOURCE,last_playable_checkpoint=recovery.ACCEPTED,
            current_round=recovery.ROUND,task_index=7,task_failures=20,failure_streak=1,
            diagnosis_used=True,overall_deadline_epoch=recovery.HARD_CAP_EPOCH,blocker=recovery.BLOCKER,
            door_fix_deferred_for_street=True,saved_door_accepted=False,second_street_attempts=1)
        before=copy.deepcopy(state);recovery.validate_pause(state);self.assertEqual(state,before)
        for key,value in [('street_submission_recovery_attempted',True),('source_checkpoint','other'),
                          ('task_failures',0),('saved_door_accepted',True),('blocker','native error')]:
            with self.subTest(key=key),self.assertRaises(Halt):recovery.validate_pause({**state,key:value})

    def test_only_complete_hash_pinned_exact_path_submission_can_be_recovered(self):
        content='x\n'*123+'y'*(6971-246)
        fields=dict(path='ConnectedStreet.cs',content=content)
        message=dict(choices=[dict(finish_reason='tool_calls',message=dict(tool_calls=[
            dict(function=dict(name='create_file',arguments=fields))]))])
        def recover(value):
            raw=json.dumps(value).encode()
            with patch.object(recovery,'RESPONSE_SHA',sha(raw)):return recovery.completed_submission(raw)
        self.assertEqual(recover(message),content)
        with self.assertRaises(Halt):recovery.completed_submission(json.dumps(message).encode())
        for field,value in [('path','../../outside.cs'),('path','WorldColliders.cs'),('content',content+'changed')]:
            altered=copy.deepcopy(message);altered['choices'][0]['message']['tool_calls'][0]['function']['arguments'][field]=value
            with self.subTest(field=field,value=value[:20]),self.assertRaises(Halt):recover(altered)
        altered=copy.deepcopy(message);altered['choices'][0]['finish_reason']='length'
        with self.assertRaises(Halt):recover(altered)
        altered=copy.deepcopy(message);altered['choices'][0]['message']['tool_calls']*=2
        with self.assertRaises(Halt):recover(altered)

    def test_tool_path_schema_names_real_choices_and_rejects_guesses(self):
        definition=tool('read_file','Read allowed source.',{'path':{'type':'string','enum':list(STREET_PATHS)}})
        for path in STREET_PATHS:
            self.assertEqual(typed_arguments(dict(name='read_file',arguments=dict(path=path)),[definition])['path'],path)
        for path in ['WorldColliders.cs','src/WorldColliders.cs','Assets/Scripts/ConnectedStreet.cs','../tests/gate.py']:
            with self.assertRaises(ValueError) as caught:typed_arguments(dict(name='read_file',arguments=dict(path=path)),[definition])
            for allowed in STREET_PATHS:self.assertIn(allowed,str(caught.exception))

    def test_visible_wall_span_does_not_select_the_prop_loop(self):
        raw=('    for (int i = 0; i < 3; i++)\n    { props(); }\n'
             '    var names = new[] { "AlleySouthWall", "AlleyNorthWall", "AlleyEndWall" };\n'
             '        for (int i = 0; i < 3; i++)\n        { walls(); }\n'
             '    if (fenceSourcePrefab != null)\n    {\n'
             '        // North (forward, +Z) end: fence runs across pavement width.\n')
        self.assertEqual(recovery.selected_span(raw,'open-old-visible-wall'),(4,4))
        self.assertEqual(recovery.selected_span(raw,'install-street'),(6,8))
        with self.assertRaises(Halt):recovery.selected_span(raw.replace('if (fenceSourcePrefab != null)','if (other)'),'install-street')
        with self.assertRaises(Halt):recovery.selected_span(raw+raw,'open-old-visible-wall')


if __name__=='__main__':unittest.main()
