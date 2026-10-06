#!/usr/bin/env python3
"""Local HUD-only correction and measured short native route legs after replay exhaustion."""
import json
import re
from resume_east_dead_drop import EastDeadDrop,PATH,TASK,ACCEPTED
from resume_three_day_queue import main
from loop_controller.core import Files,Halt,atomic,read_json,sha
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.model import tool
from loop_controller.small_edits import SelectedEdit
from loop_controller.chapter_route_probe import pilot,measured_pose,corrected_turn,full_route

SOURCE='f5b4080f64e33bf4bb563ebb573df4266c7e4f37'
ROUND='q0096-a615fc57'
RESPONSE_SHA='de90ab13284429f7b9498aae20a4ce48fa147df14be4ce26c36541e11af58b0a'

def validate_pause(old):
    expected=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=ROUND,
        task_index=7,task_failures=24,failure_streak=1,diagnosis_used=True,second_street_attempts=4,
        overall_deadline_epoch=HARD_CAP_EPOCH,chapter_negative_motion_repair_attempted=True,
        blocker='Halt: Chapter route author supplied no complete normal-input replay')
    if any(old.get(k)!=v for k,v in expected.items()) or old.get('chapter_hud_measured_route_attempted'):
        raise Halt('Expected exact preserved no-replay output exhaustion before HUD and measured-route scope')

def validate_hud(content):
    if len(content.splitlines())>85 or len(content.encode())>9000:raise ValueError('Keep the HUD replacement within85lines/9KB')
    for term in ['void Update(', 'void ActivateCache(', 'LoopInput.Replay','LoopRuntime',
                 'class LoopSignals','CreatePrimitive','Destroy(', 'SetActive(false)']:
        if term in content:raise ValueError('HUD-only scope cannot change game mechanics, hide legacy state or inspect harness: '+term)
    for field in ['RouteStage','RouteComplete','Cache','Objective','reachedInVehicle','lastRestarts']:
        if re.search(r'\b'+field+r'\s*(?:=(?!=)|\+\+|--|[+*/-]=)',content):
            raise ValueError('Keep chapter state read-only in the HUD method')
    if re.search(r'LoopSignals\.\w+\s*(?:=(?!=)|\+\+|--|[+*/-]=)',content):
        raise ValueError('Never write the protected legacy signals')
    return content

class ChapterHudMeasuredRoute(EastDeadDrop):
    def validate_recovery(self,old):
        validate_pause(old)
        raw=(self.store.root/'private/sessions'/(ROUND+'-chapter-replay')/'response-000.json').read_bytes()
        if sha(raw)!=RESPONSE_SHA:raise Halt('Original exhausted route response changed')
        choice=json.loads(raw)['choices'][0]
        if choice.get('finish_reason')!='length' or choice['message'].get('tool_calls'):
            raise Halt('No incomplete replay may be executed')
        neg=read_json(self.store.root/'evidence'/(ROUND+'-inactive-red')/'chapter-gate.json')
        if not neg.get('passed') or neg.get('candidate_commit')!=SOURCE:
            raise Halt('Require the preserved real no-handoff PASS')

    def recovery_settings(self):
        return dict(chapter_hud_measured_route_attempted=True,chapter_route_pilot_attempts=0,
            recovery_route='local-hud-readability-and-measured-normal-input-route',
            recovery_change='Preserve exhausted route role; local HUD-only edit, then at most3physical steering measurements and one full chapter route; no game or acceptance bypass')

    def source(self,ident):
        files=Files(self.project,self.store);raw=files.path(PATH).read_text()
        first=raw.index('        void BuildHud()');last=raw.index('        void Update()')
        edit=SelectedEdit(files,PATH,raw.count('\n',0,first)+1,raw.count('\n',0,last),max_lines=85)
        def save(action,f):return edit.apply(action,validate_hud(f['content']))
        self.c.update(output_tokens=6144,model_timeout_seconds=320)
        self.store.set(stage='local-chapter-hud-readability');self.store.report()
        image=self.store.root/'evidence/q0095-8506fee6-activation/captures/frame-007.png'
        self.model.session('builder',ident+'-hud',
            'You are local Qwen fixing only the visual HUD transition in your game component.',
            'Inspect the actual native activation frame. Courier DELIVERY COMPLETE dominates, while the new cyan objective '
            'is tiny and overlaps the car/bright marker. Make EAST DEAD-DROP the primary readable objective after stage1, '
            'with concise drive/exit/approach/F instructions and distance. Keep the legacy delivery receipt visibly present '
            'but visually secondary; preserve its exact completion state/text and all old tests. On R/stage0 restore its '
            'original presentation. Do not edit Mission.cs or any mechanics/state. Replace only the selected BuildHud region; '
            'you may add HUD-only fields plus a LateUpdate method here that reads RouteStage/Mode/positions and overrides '
            'hud.text after the unchanged Update. Do not redefine Update or change RouteStage,RouteComplete,Cache,Objective, '
            'reachedInVehicle,lastRestarts or LoopSignals. Existing fields/helpers are in the source below. '
            'Use existing TextMesh/LegacyRuntime.ttf. A useful readable starting layout is upper-center below the old '
            'receipt (local X0/Yabout0.4/Z1.6), font40 and characterSizeabout0.02, at most3short action lines. '
            'Use a dark backing by cloning the existing game-owned HudCard UI child, preserving the original card; '
            'do not create world primitives/new assets. Keep backing just behind text, sized to the short lines. '
            'You can cache MissionHud.transform and its original localScale, shrink the completed receipt while chapter '
            'is active and restore it in stage0. Never hide/destroy the legacy text, change its content, or move any actor. '
            'Stage2 says EAST DEAD-DROP COMPLETE, not full game completion. Do not show code coordinates or internal thresholds '
            'as the player objective. Save one <=85line replacement now, no route synthesis. '
            '\nEXACT SELECTED REGION:\n'+edit.old+'\nFULL CURRENT COMPONENT:\n'+raw,
            [tool('edit_selected_span','Save the local HUD-only layout/transition correction.',{'content':{'type':'string'}})],
            {'edit_selected_span':save},images=[('actual-activation.png ACTUAL native chapter activation',image)],
            turns=1,reasoning_effort='low')
        if files.path(PATH).read_text()==raw:raise Halt('HUD correction supplied no saved edit')
        saved=self.checkpoint_source('Local Qwen: clarify active East Dead-Drop objective HUD')
        self.store.set(source_checkpoint=saved,candidate_commit=saved);return saved

    def propose_chapter_replay(self,ident,activation):
        candidate=self.store.get('source_checkpoint');turn=1.6
        self.store.event('external-normal-input-route-composition',source_author='local Qwen',
            cloud_role='ordinary-input acceptance timing and native pose analysis only',
            reason='The one full local replay request exhausted8192tokens without a tool call')
        for attempt in range(1,4):
            self.store.set(stage='native-chapter-steering-measure',chapter_route_pilot_attempts=attempt);self.store.report()
            probe,stop=pilot(activation,turn)
            task={**TASK,'id':'chapter-steering-pilot','outcome':'Measure actual steering into the alley without declaring chapter completion.'}
            bundle,gate=self.native(task,ident+'-steering-'+str(attempt),candidate,probe)
            if not gate.get('passed'):raise Halt('Chapter steering pilot failed real native/legacy checks')
            rows=[json.loads(x) for x in (bundle/'captures/trace.jsonl').read_text().splitlines()]
            pose=measured_pose(rows,stop)
            receipt=dict(attempt=attempt,turn_seconds=turn,pose=pose,candidate=candidate,
                evidence=str(bundle.relative_to(self.store.root)),chapter_complete_claimed=False,
                cloud_role='external normal-input acceptance composition')
            atomic(bundle/'steering-observation.json',receipt);self.store.set(chapter_route_steering=receipt)
            if abs(pose['error_degrees'])<=3:
                result=full_route(activation,turn,pose)
                self.store.event('measured-chapter-route-composed',candidate=candidate,probe=result,pose=pose,
                    game_source_unchanged=True,final_game_accepted=False)
                return result
            turn=corrected_turn(turn,pose['error_degrees'])
        raise Halt('Three changed measured steering attempts did not align a clear route; preserve all native evidence')

if __name__=='__main__':raise SystemExit(main(ChapterHudMeasuredRoute))
