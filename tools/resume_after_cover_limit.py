#!/usr/bin/env python3
"""Continue the saved route after a disclosed cloud spot review of completed cover proof."""
import json
from resume_cover_evidence import CoverEvidenceResume,QUALIFIED,ACCEPTED
from resume_three_day_queue import ThreeDayRunner,main
from loop_controller.core import Halt,read_json,sha
from loop_controller.continuous_tasks import TASKS
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.replay_contract import validate_submission


def validate_cover_limit(old):
    if (old.get('source_checkpoint')!=QUALIFIED or old.get('last_playable_checkpoint')!=ACCEPTED
            or old.get('task_index')!=6 or old.get('task_failures')!=4 or old.get('failure_streak')!=2
            or old.get('overall_deadline_epoch')!=HARD_CAP_EPOCH
            or old.get('aim_complete_review',{}).get('bounded_stop')!='output'
            or old.get('blocker')!='Halt: Complete cover review remained incomplete; preserve original and new evidence'):
        raise Halt('Expected the inspected cover-review output limit; preserve other stops')


class ContinueAfterCoverLimit(CoverEvidenceResume):
    def validate_recovery(self,old):validate_cover_limit(old)
    def recovery_settings(self):return {'cover_evidence_pending':False}

    def work(self):
        bundle=self.store.root/'evidence/aim-cover-evidence-a0004565'
        contract=read_json(bundle/'aim-contract.json')
        review=read_json(bundle/'cloud-cover-review.json')
        if (not contract.get('passed') or contract.get('candidate')!=QUALIFIED
                or review.get('candidate')!=QUALIFIED or review.get('verdict')!='PASS'
                or review.get('author')!='cloud controller visual spot review'):
            raise Halt('Require the exact completed native cover proof and disclosed cloud review')
        for frame in review['images']:
            path=(self.store.root/frame['evidence']).resolve()
            if not path.is_relative_to((self.store.root/'evidence').resolve()) or sha(path.read_bytes())!=frame['sha256']:
                raise Halt('Cloud spot review must match the unchanged actual image bytes')
        proposal=self.store.root/'private/sessions/q0032-a64367b9-replay/response-000.json'
        response=read_json(proposal);choice=response['choices'][0]
        calls=[x for x in choice['message'].get('tool_calls',[]) if x['function']['name']=='finish_task']
        if choice.get('finish_reason')!='tool_calls' or len(calls)!=1:raise Halt('Expected one complete saved local replay proposal')
        saved=validate_submission(json.loads(calls[0]['function']['arguments']),TASKS[6])
        feedback=self.store.get('feedback',{})
        feedback.update(cloud_cover_spot_review=review,
            route_instruction='Independent native aim/miss/cover proof passes. Local criticism corroborated alignment/misses; cloud spot review supplied missing cover corroboration after a local output limit. Preserve the qualified thin ray and actual mission geometry. Test the already-authored normal-input route. Full-route native checks, all regressions and fresh local whole-route critique remain mandatory.')
        self.store.set(cover_saved_replay_pending=saved,cloud_cover_spot_review=review,feedback=feedback)
        self.store.event('continue-after-cover-review-limit',candidate=QUALIFIED,
            original_local_reviews_preserved=True,cloud_review_disclosed=True,
            game_source_mutation=False,task_counters_changed=False,whole_route_promoted=False,
            replay_response_sha256=sha(proposal.read_bytes()))
        return ThreeDayRunner.work(self)


if __name__=='__main__':raise SystemExit(main(ContinueAfterCoverLimit))

