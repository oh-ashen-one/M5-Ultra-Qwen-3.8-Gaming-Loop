#!/usr/bin/env python3
"""Preserve pre-request context rejection; separate mechanics and art image sets."""
from resume_chapter_review_street_details import ChapterReviewStreetDetails,SOURCE,ACCEPTED
from resume_three_day_queue import main
from loop_controller.core import Halt,read_json
from loop_controller.delivery_policy import HARD_CAP_EPOCH

def validate_pause(old):
    expected=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round='q0099-518ae4f9',
        task_index=7,task_failures=24,failure_streak=1,diagnosis_used=True,second_street_attempts=4,
        overall_deadline_epoch=HARD_CAP_EPOCH,chapter_review_street_details_attempted=True,
        blocker='Halt: Corrected chapter review supplied no complete verdict')
    if any(old.get(k)!=v for k,v in expected.items()) or old.get('chapter_review_context_repair_attempted'):
        raise Halt('Require exact pre-inference image-budget rejection')
    review=old.get('east_dead_drop_corrected_review',{}).get('review',{})
    if review.get('bounded_stop')!='context':raise Halt('Do not retry a different critic failure')

class ChapterReviewContext(ChapterReviewStreetDetails):
    def validate_recovery(self,old):
        validate_pause(old);self.verify_original()
        session=self.store.root/'private/sessions/q0099-518ae4f9-critic'
        if any(session.iterdir()):raise Halt('Expected no inference request or generated response')
        if read_json(self.store.root/'evidence/q0099-518ae4f9/critic.json').get('bounded_stop')!='context':
            raise Halt('Preserve the actual context rejection')

    def recovery_settings(self):
        return {**super().recovery_settings(),'chapter_review_context_repair_attempted':True,
            'recovery_change':'Keep65536working context and8192output budgets: five actual chapter frames without style reference; facade review uses four chapter frames plus style reference. Original rejection preserved.'}

if __name__=='__main__':raise SystemExit(main(ChapterReviewContext))
