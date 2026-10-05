#!/usr/bin/env python3
"""Revalidate an existing native-passing review rejected solely for verdict casing."""
import json

from continue_game_queue import validate_scoped_review
from loop_controller.core import Halt,atomic,read_json,sha
from loop_controller.continuous_checks import evaluate_step
from loop_controller.continuous_tasks import TASKS
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.model import tool,typed_arguments
from loop_controller.runner import git
from resume_failure_retry import ACCEPTED_COURIER
from resume_three_day_queue import ThreeDayRunner,main

RESTORED_SOURCE='cc8522d604ccdddd6704e138ba54e05ac9acefde'
PASSED_SOURCE='9eeda604c64be6da33e0f566c7e8bc523dbf8251'
EVIDENCE='q0023-7c24fc89'


def validate_case_pause(state):
    if (state.get('task_index')!=3 or state.get('source_checkpoint')!=RESTORED_SOURCE
            or state.get('last_playable_checkpoint')!=ACCEPTED_COURIER
            or state.get('task_failures')!=6 or state.get('diagnosis_used') is not True
            or state.get('feedback',{}).get('bounded_stop')!='context'
            or state.get('overall_deadline_epoch')!=HARD_CAP_EPOCH
            or state.get('blocker')!='Halt: Repeated diagnosed blocker on mission-failure-retry; failed source preserved and last playable state restored'):
        raise Halt('Only the exact inspected review-format rejection may be revalidated')


def revalidate_review(response,names):
    choice=response['choices'][0];calls=choice.get('message',{}).get('tool_calls',[])
    if choice.get('finish_reason')!='tool_calls' or len(calls)!=1 or calls[0]['function']['name']!='submit_review':
        raise Halt('Expected one completed saved review submission, not a partial model response')
    function=dict(calls[0]['function'])
    if isinstance(function['arguments'],str):function['arguments']=json.loads(function['arguments'])
    schema=tool('submit_review','Validate the saved scoped review.',{
        'verdict':{'type':'string'},'summary':{'type':'string'},'fixes':{'type':'array','items':{'type':'string'}}})
    fields=typed_arguments(function,[schema])
    result=validate_scoped_review(fields,names)
    if fields['verdict']!='pass' or result['verdict']!='PASS':
        raise Halt('Preserve every review except the inspected lower-case pass')
    return result


class CaseReviewRunner(ThreeDayRunner):
    def validate_recovery(self,old):validate_case_pause(old)

    def recovery_settings(self):return {'review_case_revalidation_pending':True}

    def work(self):
        if not self.store.get('review_case_revalidation_pending'):raise Halt('Review revalidation is a one-time operation')
        bundle=self.store.root/'evidence'/EVIDENCE;task=TASKS[3]
        gate=read_json(bundle/'scoped-gate.json')
        if not gate.get('passed') or gate.get('candidate_commit')!=PASSED_SOURCE:
            raise Halt('Preserve a candidate without the saved native PASS')
        regression=gate.get('regressions',{})
        if (not regression.get('passed') or {v['test'] for v in regression.get('regressions',[])}!={'walk','world','motor','courier'}
                or not all(v['gate'].get('passed') and v['gate'].get('candidate_commit')==PASSED_SOURCE for v in regression['regressions'])):
            raise Halt('All four genuine regressions must already pass this exact source')
        if not evaluate_step(task,bundle,gate).get('passed'):raise Halt('Saved mission trace no longer passes unchanged native checks')
        starts=[json.loads(x) for (x,) in self.store.db.execute("SELECT data FROM events WHERE kind='role-start'")
                if json.loads(x).get('session_id')==EVIDENCE+'-critic']
        if len(starts)!=1:raise Halt('Expected the exact saved fresh critic image provenance')
        names=[]
        for record in starts[0]['images']:
            if record['label'].startswith('ACTUAL NATIVE UNITY '):
                path=bundle/'captures'/record['name'];names.append(record['name'])
            elif record['label'].startswith('AI-GENERATED CHICAGO TARGET;'):path=self.refs/record['name']
            else:raise Halt('Unknown review image provenance')
            if sha(path.read_bytes())!=record['sha256']:raise Halt('Previously reviewed image changed')
        response=self.store.root/'private/sessions'/(EVIDENCE+'-critic')/'response-000.json'
        review=revalidate_review(read_json(response),names)
        self.store.event('review-case-revalidated',original_verdict='pass',canonical_verdict='PASS',
            response_sha256=sha(response.read_bytes()),new_inference=False,new_game_attempt=False,
            native_evidence=EVIDENCE,preserved_task_failures=self.store.get('task_failures'))
        atomic(bundle/'critic-revalidated.json',review)
        self.machine.guard()
        git(self.repo,'restore','--source',PASSED_SOURCE,'--staged','--worktree','--','game')
        git(self.repo,'-c','user.name=Evidence controller','-c','user.email=254017794+oh-ashen-one@users.noreply.github.com',
            'commit','-m','Restore native-passing local source after review format correction')
        if git(self.repo,'rev-parse','HEAD:game')!=git(self.repo,'rev-parse',PASSED_SOURCE+':game'):
            raise Halt('Restored game tree differs from the native-tested source')
        self.promote(task,PASSED_SOURCE,bundle,gate,review)
        receipt=self.store.root/'milestones/delivery-receipts/q0023-private-library.json'
        if receipt.exists():
            delivery=read_json(receipt);outbox=self.store.root/'milestones/outbox'/(EVIDENCE+'--accepted-feature.json')
            record=read_json(outbox)
            if record['build_id']!=delivery['build_id']:raise Halt('Screenshot delivery belongs to another build')
            record.update(library_files=delivery['library_files'],delivery_status=delivery['delivery_status'],final_visual_quality_accepted=False)
            atomic(outbox,record)
        self.store.set(review_case_revalidation_pending=False)
        # Promotion, rather than another gameplay retry, advances to the next authorized task.
        return super().work()


if __name__=='__main__':raise SystemExit(main(CaseReviewRunner))
