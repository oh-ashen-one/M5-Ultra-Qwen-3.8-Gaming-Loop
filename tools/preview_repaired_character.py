#!/usr/bin/env python3
"""Early export/native preview of the focused local character correction."""
from preview_clothed_character import PreviewClothedCharacter
from author_clothed_character import ACCEPTED,SAVED
from repair_clothed_character_export import SOURCE
from resume_three_day_queue import main
from loop_controller.core import Halt
from loop_controller.delivery_policy import HARD_CAP_EPOCH


def validate_boundary(old):
    expected=dict(status='paused',controller_pid=None,owned_process=None,last_playable_checkpoint=ACCEPTED,
        task_index=7,task_failures=24,failure_streak=1,diagnosis_used=True,
        overall_deadline_epoch=HARD_CAP_EPOCH,blocker=SAVED,clothed_character_export_repair_attempted=True)
    result=old.get('clothed_character_source_outcome',{})
    if (any(old.get(k)!=v for k,v in expected.items()) or old.get('clothed_character_repaired_preview_attempted')
            or result.get('repaired_prior_source')!=SOURCE or not result.get('local_authored')
            or result.get('candidate')!=old.get('source_checkpoint')):
        raise Halt('Require the saved local export repair and preserved first export failure')


class PreviewRepairedCharacter(PreviewClothedCharacter):
    def validate_recovery(self,old):
        validate_boundary(old);self.source=old['source_checkpoint'];self.source_result=old['clothed_character_source_outcome']
        self.resume_capacity=self.priority_resume=self.transport_recovery=self.admission_recovery=False

    def recovery_settings(self):
        return dict(clothed_character_repaired_preview_attempted=True,
            recovery_route='early-native-preview-after-local-export-repair',
            recovery_change='Same accepted fallback and preserved failed first export. Inference stays unloaded while the locally repaired original character is exported and viewed before animation integration.')


if __name__=='__main__':raise SystemExit(main(PreviewRepairedCharacter))
