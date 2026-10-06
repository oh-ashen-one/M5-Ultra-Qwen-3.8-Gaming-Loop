#!/usr/bin/env python3
"""Recover an already accepted local diagnosis after a terminal-tool routing bug."""
import json
from resume_camera_branch_diagnosis import CameraBranchDiagnosis, SOURCE, ACCEPTED, SPANS
from resume_three_day_queue import main
from loop_controller.core import Halt, atomic, read_json, sha
from loop_controller.delivery_policy import HARD_CAP_EPOCH

ROUND='q0090-cdb1642f'
RESPONSE_SHA='4a7206bd9a750161cd8425a7998c1dba804c4f70783eee911eaf5208c91e594c'
OBSERVATION_SHA='2026341f3120c6dff342d7dac2070b569121c100d1df74d92aba9d15cb646f30'
GATE_SHA='fe6a552637a76f58592e13c85d5145a3afd61f36cadba74baa328f352c8ced1b'
STOP_SHA='62f85d4b344477444e1b845f07d78b8f4ecdf29ad3f859e74e15384ca6cf7f08'


def validate_pause(old):
    expected=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=ROUND,
        task_index=7,task_failures=23,failure_streak=1,diagnosis_used=True,second_street_attempts=4,
        overall_deadline_epoch=HARD_CAP_EPOCH,camera_branch_diagnosis_attempted=True,
        blocker='Halt: Local branch diagnosis supplied no complete findings; preserve observations before any edit')
    if any(old.get(k)!=v for k,v in expected.items()) or old.get('completed_camera_diagnosis_recovered'):
        raise Halt('Expected exact accepted-diagnosis return-routing stop')


def completed_diagnosis(raw,history):
    if sha(raw)!=RESPONSE_SHA:raise Halt('Original complete diagnosis response changed')
    choice=json.loads(raw)['choices'][0];calls=choice['message'].get('tool_calls',[])
    if choice.get('finish_reason')!='tool_calls' or len(calls)!=1 or calls[0]['function']['name']!='submit_diagnosis':
        raise Halt('Require one complete original diagnosis tool call, never truncated output')
    fields=json.loads(calls[0]['function']['arguments'])
    if (set(fields)!={'cause','span','minimal_change'} or fields['span'] not in SPANS
        or any(not isinstance(fields[k],str) or not fields[k].strip() or len(fields[k])>1800 for k in ['cause','minimal_change'])):
        raise Halt('Original diagnosis does not meet its original concise contract')
    results=[m for m in history if m.get('role')=='tool' and m.get('tool_call_id')==calls[0]['id']]
    result=dict(ok=True,**fields)
    if len(results)!=1 or json.loads(results[0]['content'])!=result:
        raise Halt('Original diagnosis was not successfully accepted by its tool')
    return result


class CompletedCameraDiagnosis(CameraBranchDiagnosis):
    def validate_recovery(self,old):
        validate_pause(old);self.saved_diagnosis();self.sealed_probe();self.accepted_probe()

    def saved_diagnosis(self):
        bundle=self.store.root/'evidence'/(ROUND+'-branch-diagnostic')
        for name,digest in [('return-branch-observation.json',OBSERVATION_SHA),('gate.json',GATE_SHA),('local-cause-diagnosis.json',STOP_SHA)]:
            if sha((bundle/name).read_bytes())!=digest:raise Halt('Preserved branch diagnostic evidence changed')
        observed=read_json(bundle/'return-branch-observation.json');gate=read_json(bundle/'gate.json')
        if observed.get('source')!=SOURCE or observed.get('passive_trace_equivalent') is not True or not gate.get('passed'):
            raise Halt('Require completed equivalent native branch observation')
        session=self.store.root/'private/sessions'/(ROUND+'-cause-diagnosis')
        result=completed_diagnosis((session/'response-000.json').read_bytes(),read_json(session/'history.json'))
        return result,observed

    def recovery_settings(self):
        return dict(completed_camera_diagnosis_recovered=True,recovery_route='accepted-local-diagnosis-return-recovery',
            recovery_change='Preserve terminal-tool routing failure; reuse exact accepted local cause/action without repeating inference')

    def diagnose(self,ident):
        result,observed=self.saved_diagnosis()
        atomic(self.store.root/'diagnosis-recovery'/(ident+'.json'),dict(original_round=ROUND,
            original_response_sha256=RESPONSE_SHA,diagnosis=result,original_tool_accepted=True,
            inference_repeated=False,findings_changed=False,private_reasoning_used=False))
        self.store.set(camera_local_cause_diagnosis=result,camera_branch_observation=observed)
        self.store.event('accepted-local-camera-diagnosis-recovered',original_round=ROUND,
            response_sha256=RESPONSE_SHA,findings_changed=False,inference_repeated=False)
        return result,observed


if __name__=='__main__':raise SystemExit(main(CompletedCameraDiagnosis))
