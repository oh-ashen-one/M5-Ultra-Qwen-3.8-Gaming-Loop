#!/usr/bin/env python3
"""Reuse sealed street inputs, qualify saved fence, and scope local camera repair."""
import json
from resume_saved_door import SavedDoor, SECOND_TASK, ACCEPTED
from resume_three_day_queue import main
from repair_camera_clearance import CameraRepair
from qualify_map_extension import inspect_extension, promote_qualified_extension
from qualify_visual_replay import REGRESSIONS
from loop_controller.core import Files, Halt, atomic, read_json, sha, verify_seal
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.features import pavement_coverage
from loop_controller.model import tool
from loop_controller.small_edits import SelectedEdit
from loop_controller.runner import git

SOURCE='b651a9fbdd8f2944fa773640b1d31a11f3e61752'
BASE='6f9244b9045039e0749cd85489e55114b345e448'
ROUND='q0086-1628aaff'
EVIDENCE='q0085-cafbd6d3'
RESPONSE_SHA='6f6be45ba2c73bdb451dfff89e31b322bddebb6dfecd096a13039c285883d9f8'
MANIFEST_SHA='9af685165bb7a328c2e512f2ce5916f1dd7f3ec4cf96cc76fb48f412d2a8cb0b'
GATE_SHA='98d8a771c0bb2de7026e2197b2308fbda9ef17774dc6a09d8a9fe309905271f1'
CRITIC_SHA='6f3e90db713549e5667cd7144eb490c2704b73c3afc3552e7ec313ce06373579'
SCENARIO_SHA='e3affe7d53ae4f4de5aefeb24f849826ac98430dce21ebe56e6442eda0c92081'


def validate_pause(old):
    expected=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=ROUND,
        task_index=7,task_failures=23,failure_streak=1,diagnosis_used=True,
        overall_deadline_epoch=HARD_CAP_EPOCH,second_street_attempts=4,saved_door_accepted=False,
        blocker='Halt: Second-street replay supplied no complete bounded tool submission')
    if any(old.get(k)!=v for k,v in expected.items()) or old.get('street_readability_recovery_attempted'):
        raise Halt('Expected exact saved fence and exhausted replay pause; preserve other faults')


def require_sealed_native(gate,manifest,review):
    tests=gate.get('regressions',{}).get('regressions',[])
    if (not gate.get('passed') or gate.get('candidate_commit')!=BASE
        or not gate.get('scene_inventory',{}).get('passed')
        or manifest.get('candidate')!=BASE or manifest.get('scope')!=SECOND_TASK['id']
        or len(tests)!=10 or {t.get('test') for t in tests}!=REGRESSIONS
        or not all(t.get('gate',{}).get('passed') and t['gate'].get('candidate_commit')==BASE for t in tests)
        or not review.get('ok') or review.get('verdict')!='FIX'):
        raise Halt('Require complete prior native mechanics plus the preserved visual FIX; no verdict upgrade')


def validate_camera_span(content):
    if any(x in content for x in ['LoopCamera','LoopInput','LoopSignals','CameraClearanceWall',
            'Destroy(','.enabled = false','.enabled=false','public class','namespace ']):
        raise ValueError('Only ordinary camera geometry inside the selected method; no test branches or collider disabling')


class StreetReadability(SavedDoor):
    def validate_recovery(self,old):
        validate_pause(old)
        raw=(self.store.root/'private/sessions'/(ROUND+'-street-replay')/'response-000.json').read_bytes()
        if sha(raw)!=RESPONSE_SHA:raise Halt('Original exhausted replay changed')
        choice=json.loads(raw)['choices'][0]
        if choice.get('finish_reason')!='length' or choice['message'].get('tool_calls'):
            raise Halt('Expected preserved output exhaustion without executable inputs')
        changed=git(self.repo,'diff','--name-only',BASE,SOURCE,'--','game').splitlines()
        if changed!=['game/Assets/Game/ConnectedStreet.cs']:
            raise Halt('Saved fence recovery must not include unrelated game changes')
        self.sealed_probe()
        self.accepted_probe()

    def sealed_probe(self):
        bundle=self.store.root/'evidence'/EVIDENCE
        for name,expected in [('scoped-gate.json',GATE_SHA),('critic.json',CRITIC_SHA),
                              ('captures/scenario.json',SCENARIO_SHA)]:
            if sha((bundle/name).read_bytes())!=expected:raise Halt('Sealed street evidence changed: '+name)
        manifest=verify_seal(bundle/'captures',MANIFEST_SHA)
        require_sealed_native(read_json(bundle/'scoped-gate.json'),manifest,read_json(bundle/'critic.json'))
        return read_json(bundle/'captures/scenario.json')

    def recovery_settings(self):
        return dict(street_readability_recovery_attempted=True,
            recovery_route='sealed-street-inputs-focused-local-camera',
            recovery_change='Preserve replay exhaustion and visual FIX; freshly test saved fence, then local camera span and all native gates')

    def reuse_probe(self,candidate):
        probe=self.sealed_probe()
        self.store.event('reuse-sealed-native-street-inputs',candidate=candidate,
            original_candidate=BASE,source_evidence=EVIDENCE,scenario_sha256=SCENARIO_SHA,
            manifest_sha256=MANIFEST_SHA,prior_visual_verdict='FIX',
            current_candidate_requires_fresh_native=True,all_acceptance_criteria_preserved=True,
            game_author='local Qwen',replay_reuse_author='cloud controller infrastructure')
        return probe

    def camera_edit(self,ident):
        files=Files(self.project,self.store);path='Assets/Game/Bootstrap.cs';raw=files.path(path).read_text()
        start='            // Final geometry-aware near-plane guard:'
        end='            transform.position = pos;'
        if raw.count(start)!=1 or raw.count(end)!=1:raise Halt('Expected exact final camera-clearance span')
        first=raw.count('\n',0,raw.index(start))+1;last=raw.count('\n',0,raw.index(end))
        edit=SelectedEdit(files,path,first,last,max_lines=110)
        follow=raw[raw.index('    public class Follow'):]
        def save(action,fields):
            validate_camera_span(fields['content']);return edit.apply(action,fields['content'])
        self.c.update(output_tokens=6144,model_timeout_seconds=300)
        self.store.set(stage='local-street-return-camera-repair');self.store.report()
        self.model.session('builder',ident+'-camera-span',
            'You are the sole local Qwen camera author. Save one focused geometry correction using the exact selected source span.',
            'Actual street replay t50.50 shows the camera embedded in the coupe roof/body during reverse return near a wall. '
            'Camera is near(1.89,1.77,15.57), car root(3.89,-0.01,15.83); target bounds straddle the near plane. '
            'The current final guard ignores own target colliders and only corrects foreign overlaps by moving toward the target. '
            'Fix the final lens/near-plane pose so it clears both the followed vehicle visual body and nearby world geometry, '
            'with readable framing in cramped space. Preserve normal open-space camera behavior, target cache, public fields, '
            'floor safety, controls, aim, mission, boarding and actual target motion. Use ordinary world geometry/renderer bounds; '
            'no hardcoded test coordinates, replay times or fixture names. Do not disable colliders. '
            'Only the supplied final-clearance block may change; the following transform.position assignment and look logic remain. '
            'All close-wall, entry/exit/aim and full street tests will run fresh. Submit edit_selected_span now; no replay authoring. '
            '\nSELECTED OLD BLOCK:\n'+edit.old+'\nFULL CURRENT FOLLOW FOR CONTEXT:\n'+follow,
            [tool('edit_selected_span','Save the selected final camera-clearance block.',{'content':{'type':'string'}})],
            {'edit_selected_span':save},turns=1,reasoning_effort='low')
        if files.path(path).read_text()==raw:raise Halt('Focused local camera role saved no correction; preserve fence and evidence')
        candidate=self.checkpoint_source('Local Qwen: clear coupe body during cramped street return')
        self.store.set(source_checkpoint=candidate,candidate_commit=candidate)
        return candidate

    def work(self):
        ident=self.begin(SECOND_TASK,'saved-fence-native-diagnostic')
        bundle,gate=self.native(SECOND_TASK,ident,SOURCE,self.reuse_probe(SOURCE))
        if not gate.get('passed'):
            self.record_rejection(SECOND_TASK,ident,SOURCE,gate)
            raise Halt('Saved fence failed fresh native gate; preserve exact game failure')
        rows=[json.loads(x) for x in (bundle/'captures/trace.jsonl').read_text().splitlines()]
        diagnostic=dict(candidate=SOURCE,build_id=gate['build_id'],
            traversal=inspect_extension(rows,SECOND_TASK['prior_bounds']),support=pavement_coverage(bundle),
            full_acceptance=False,reason='Focused fence diagnostic before known camera FIX; full suite and critique follow the camera edit')
        atomic(bundle/'fence-diagnostic.json',diagnostic)
        if not diagnostic['traversal']['passed'] or not diagnostic['support']['passed']:
            raise Halt('Saved fence altered verified physical traversal or support; preserve diagnostic')
        self.store.set(saved_fence_native_diagnostic=diagnostic)
        ident=self.begin(SECOND_TASK,'focused-local-camera-and-street-qualification')
        candidate=self.camera_edit(ident)
        _,camera=CameraRepair.camera_probe(self,ident+'-camera-clearance',candidate)
        if not camera['passed']:raise Halt('Focused street camera edit failed existing near/middle/endpoint wall contracts')
        bundle,gate,failure=self.qualify(SECOND_TASK,ident,candidate,self.reuse_probe(candidate))
        if failure:
            self.record_rejection(SECOND_TASK,ident,candidate,failure)
            raise Halt('Focused camera/street qualification needs the recorded native or visual correction; accepted connector preserved')
        record=promote_qualified_extension(self,SECOND_TASK,bundle,gate,read_json(bundle/'critic.json'))
        return self.continue_after_street(record)


if __name__=='__main__':raise SystemExit(main(StreetReadability))
