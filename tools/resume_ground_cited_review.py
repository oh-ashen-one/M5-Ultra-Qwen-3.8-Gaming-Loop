#!/usr/bin/env python3
"""Validate the exact completed local ground verdict, then resume local mission design."""
import json
from resume_street_ground import StreetGround,GROUND_TASK,ACCEPTED
from resume_three_day_queue import main
from continue_game_queue import review_captures,validate_scoped_review
from loop_controller.core import Halt,atomic,read_json,sha,verify_seal
from loop_controller.delivery_policy import HARD_CAP_EPOCH

SOURCE='248c1cd14db9b70da9ce354f21b5a8afeab35cee'
ROUND='q0107-68764670'
RESPONSE_SHA='8a6e725edf561ff300e7d3ca84cb02d7cd6c5a72f2afa7ddeca8a7a2e20d2a7a'
HASHES={'chapter-gate.json':'8b6f0b64b09ece8e9e69cc13c2d76299df705e7355cad1a0e62d27e03c5d2515',
    'ground-gate.json':'479104e21aeda7ac59288f42fb26a9d2a5208a33425ce54ba13a10e5b3261caf',
    'captures/manifest.json':'f57c8d588c6abd8edcbe4c82e1f160eb4931f779fa092e64f60e8c3132ac6647',
    'critic.json':'dc3c72c52c75df65ae5f50d169d3263e1ae0a53fe9d3c6a92b41210edf8eab09',
    'ground-outcome.json':'85189de49116b595845ab282a382b0fbd5913b5a242d7a4d857fdfb8a2cde9d1'}

def validate_pause(old):
    expected=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=ROUND,
        task_index=7,task_failures=24,failure_streak=1,diagnosis_used=True,second_street_attempts=4,
        overall_deadline_epoch=HARD_CAP_EPOCH,stage='fresh-ground-critique',
        blocker='Halt: Ground critic supplied no complete verdict')
    if any(old.get(k)!=v for k,v in expected.items()) or old.get('ground_cited_review_recovered'):
        raise Halt('Require exact ground citation/context stop and unchanged history')
    if old.get('street_ground_outcome',{}).get('review',{}).get('bounded_stop')!='context':
        raise Halt('Preserve a different ground critic outcome')

def recover_review(raw,times):
    if sha(raw)!=RESPONSE_SHA:raise Halt('Original ground critic response changed')
    c=json.loads(raw)['choices'][0];calls=c['message'].get('tool_calls',[])
    if c.get('finish_reason')!='tool_calls' or len(calls)!=1 or calls[0]['function']['name']!='submit_review':
        raise Halt('Require one complete original local verdict tool call')
    fields=json.loads(calls[0]['function']['arguments'])
    review=validate_scoped_review(fields,list(times),times)
    if review['verdict']!='PASS' or set(review.get('verified_capture_time_citations',{}))!=set(times):
        raise Halt('Require the original PASS to cite every supplied actual capture unambiguously')
    if any(review[k]!=fields[k] for k in ('verdict','summary','fixes')):
        raise Halt('Never rewrite the independent verdict')
    return review

class GroundCitedReview(StreetGround):
    def response(self):
        return (self.store.root/'private/sessions'/(ROUND+'-critic')/'response-000.json').read_bytes()

    def validate_recovery(self,old):
        validate_pause(old);self.verify_presentation()
        e=self.store.root/'evidence'/ROUND
        for name,digest in HASHES.items():
            if sha((e/name).read_bytes())!=digest:raise Halt('Preserve original ground evidence: '+name)
        verify_seal(e/'captures',HASHES['captures/manifest.json'])
        g=read_json(e/'chapter-gate.json');regs=g.get('regressions',{}).get('regressions',[])
        if (not g.get('passed') or g.get('candidate_commit')!=SOURCE or len(regs)!=10 or
            not all(x['gate'].get('passed') and x['gate'].get('candidate_commit')==SOURCE for x in regs) or
            not read_json(e/'ground-gate.json').get('passed')):
            raise Halt('Require all current-source native ground/chapter and legacy passes')
        _,times=review_captures(GROUND_TASK,e);recover_review(self.response(),times)

    def recovery_settings(self):
        return dict(ground_cited_review_recovered=True,recovery_route='validate-completed-ground-time-citations',
            recovery_change='Validate seconds-suffixed citations against sealed frame times; preserve exact original local verdict and context rejection, then corrected local mission design. No native rerun or new critic inference.')

    def work(self):
        self.machine.guard()
        original=self.store.root/'evidence'/ROUND
        _,times=review_captures(GROUND_TASK,original);review=recover_review(self.response(),times)
        ident=self.begin(GROUND_TASK,'recover-complete-ground-critic')
        bundle=self.store.root/'evidence'/ident;bundle.mkdir()
        record=dict(candidate=SOURCE,evidence=str(original.relative_to(self.store.root)),native_pass=True,
            review=review,accepted=True,final_game_accepted=False,original_response_sha256=RESPONSE_SHA,
            original_failure_preserved=True,new_critic_inference=False)
        atomic(bundle/'ground-outcome.json',record)
        atomic(bundle/'evidence-reuse.json',dict(original_round=ROUND,hashes=HASHES,native_rerun=False))
        self.store.set(street_ground_outcome=record)
        self.store.event('ground-completed-verdict-validated',**record);self.store.report()
        self.revised_plan(ident);self.store.report()
        raise Halt('Ground scope and corrected next gameplay design saved; seal additive mission acceptance before implementation')

if __name__=='__main__':raise SystemExit(main(GroundCitedReview))
