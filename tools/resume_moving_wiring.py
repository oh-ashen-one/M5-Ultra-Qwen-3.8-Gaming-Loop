#!/usr/bin/env python3
"""Recover exact local wiring and repair small actual-API/source defects locally."""
import json
from resume_moving_encounter import MovingEncounter, PATH, HUD, TASK, exploratory_probe
from resume_hud_presentation_polish import compact
from resume_combat_death import ACCEPTED
from resume_three_day_queue import main
from loop_controller.core import Halt, Files, atomic, read_json, sha
from loop_controller.small_edits import SelectedEdit
from loop_controller.delivery_policy import HARD_CAP_EPOCH

SOURCE='c5710b0d09742082502180226aad8f937e3b0775'
ROUND='q0124-449aee98'
RESPONSE='5d3217b83985d55e6ee04e85f84de86da24106877738a7b14da5234b1be16838'


def wiring(raw):
    if sha(raw)!=RESPONSE: raise Halt('Preserve the complete original local HUD wiring submission')
    choice=json.loads(raw)['choices'][0]; calls=choice['message'].get('tool_calls',[])
    if choice['finish_reason']!='tool_calls' or len(calls)!=1 or calls[0]['function']['name']!='finish_source':
        raise Halt('Require the complete public source tool submission')
    value=json.loads(calls[0]['function']['arguments'])['content']
    expected='var _interception = FindAny<InterceptionMission>();\nstring s = null;\nif (_interception != null && _interception.Active) s = _interception.Objective;\nelse if (_relay != null && _relay.Active)'
    if compact(value)!=compact(expected): raise Halt('Only the intended actual-state lookup/priority wiring is recoverable')
    return value


def validate_pause(old):
    expected=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=ROUND,
        task_index=7,task_failures=24,failure_streak=1,diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,
        stage='local-hud-polish-moving-encounter-current-objective',
        blocker='Halt: Local HUD correction not saved: moving-encounter-current-objective: '+json.dumps(
            {'bounded_stop':'turns','summary':'Tool-turn budget exhausted; preserve partial work for the next task.'}))
    if any(old.get(k)!=v for k,v in expected.items()) or old.get('moving_wiring_recovered'):
        raise Halt('Require exact completed local encounter wiring rejection and preserved history')


class MovingWiring(MovingEncounter):
    def validate_recovery(self,old):
        validate_pause(old)
        self.resume_capacity=False; self.priority_resume=False; self.transport_recovery=False
        self.admission_recovery=False
        self.saved_wiring=wiring((self.store.root/'private/sessions'/
            'q0124-449aee98-moving-encounter-current-objective/response-000.json').read_bytes())

    def recovery_settings(self):
        return dict(moving_wiring_recovered=True,recovery_route='exact-local-wiring-and-tiny-API-repairs',
            recovery_change='Recover the complete local temporary-variable HUD lookup, which was rejected '
            'only for differing from a cached-field spelling. Then local Qwen fixes the actual float Health '
            'read, initializes the first objective, keeps ending receipts, and faces actual movement. '
            'Prior rejected tool responses and original accepted checkpoints remain unchanged.')

    def source(self,ident):
        raw=(self.project/HUD).read_text()
        old='            string s = null;\n            if (_relay != null && _relay.Active)'
        if raw.count(old)!=1: raise Halt('Require exact unmodified HUD selection span')
        first=raw[:raw.index(old)].count('\n')+1
        SelectedEdit(Files(self.project,self.store),HUD,first,first+1,max_lines=6).apply(
            ident+'-recover-complete-wiring',self.saved_wiring)
        self.store.event('complete-local-moving-wiring-recovered',response_sha256=RESPONSE,private_reasoning_used=False,
            source_authored_by='local-Qwen',different_lookup_spelling=True)
        candidate=self.checkpoint_source('Local Qwen: recover complete moving encounter objective wiring')
        self.store.set(source_checkpoint=candidate,candidate_commit=candidate)
        raw=(self.project/PATH).read_text(); start=raw.index('        int ReadHealth()'); end=raw.index('\n        }',start)+len('\n        }')
        old=raw[start:end]
        expected='float ReadHealth() { return LoopSignals.Health; }'
        self.patch(ident,'actual-float-health-api',PATH,old,
            'Actual public LoopSignals.Health is float, not int. Replace this whole helper with '
            'float ReadHealth() { return LoopSignals.Health; } only. No fallback, reflection, cast or state write.',
            lambda value,_:compact(value)==compact(expected),3)
        raw=(self.project/PATH).read_text(); old=next(s for s in raw.splitlines(True) if 'Active = true; armedAt = Time.time;' in s)
        expected=old.replace('armedAt = Time.time;', 'armedAt = Time.time; UpdateObj();')
        self.patch(ident,'initialize-first-encounter-objective',PATH,old,
            'This activation sets Active but returns with Objective=null, so the higher-priority MissionBoard '
            'can be blank for its first frame. Append UpdateObj(); immediately after armedAt=Time.time; '
            'inside this same conditional. Preserve the actual relay condition, timing and flags.',
            lambda value,_:compact(value)==compact(expected),2)
        raw=(self.project/PATH).read_text(); old=next(s for s in raw.splitlines(True) if 'go.transform.rotation = Quaternion.identity;' in s)
        expected=old.replace('Quaternion.identity','Quaternion.LookRotation(Vector3.right, Vector3.up)')
        self.patch(ident,'runners-face-real-motion',PATH,old,
            'Runners move along world +X. Replace only Quaternion.identity with Quaternion.LookRotation(Vector3.right, Vector3.up) '
            'so original actor meshes face their real movement. No position, scale, collider or velocity change.',
            lambda value,_:compact(value)==compact(expected),2)
        raw=(self.project/PATH).read_text(); start=raw.index('        void UpdateObj()'); end=raw.index('        void Cleanup()',start)
        old=raw[start:end]
        expected=old.replace('INTERCEPT RUNNERS 3/3','INTERCEPTION COMPLETE').replace('"MISSION FAILED\\n"','"INTERCEPTION FAILED\\n"').replace('\\nR reset"','\\nRelay complete | R reset"')
        self.patch(ident,'truthful-encounter-endings',PATH,old,
            'Preserve all conditions, count expressions and active-phase text. Change completed heading '
            'INTERCEPT RUNNERS 3/3 to INTERCEPTION COMPLETE; failed heading MISSION FAILED to INTERCEPTION FAILED; '
            'in ending/failure strings replace final newline R reset with newline Relay complete | R reset. '
            'No new line beyond the existing four; no state changes.',
            lambda value,_:compact(value)==compact(expected),15)
        return self.store.get('source_checkpoint')

    def work(self):
        ident=self.begin(TASK,'local-moving-encounter-focused-repairs'); candidate=self.source(ident)
        original=read_json(self.store.root/'evidence/q0120-dc4867c8-positive/captures/scenario.json')
        self.store.set(stage='native-moving-encounter-exploration'); self.store.report()
        bundle=self.store.root/'evidence'/(ident+'-exploration')
        gate=self.engines.unity(self.project,bundle,exploratory_probe(original),candidate)
        result=dict(candidate=candidate,evidence=str(bundle.relative_to(self.store.root)),native=gate,
            gameplay_qualified=False,secondary_target_isolation_qualified=False,final_game_accepted=False)
        atomic(bundle/'moving-encounter-exploration.json',result)
        self.store.set(moving_encounter_exploration=result); self.store.report()
        if not gate.get('passed'): raise Halt('Moving encounter first native evidence requires measured diagnosis')
        from qualify_moving_encounter import qualify
        qualify(self,ident,candidate,bundle,gate,original)


if __name__=='__main__': raise SystemExit(main(MovingWiring))
