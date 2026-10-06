#!/usr/bin/env python3
"""Repair measured live-window HUD bounds and a duplicated cache ground offset."""
from resume_chapter_presentation import ChapterPresentation,PATH,validate_visual_span,ACCEPTED
from resume_three_day_queue import main
from loop_controller.core import Files,Halt,read_json,sha
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.model import tool
from loop_controller.small_edits import SelectedEdit

SOURCE='47e1b8a7bf210268f99deb884b3bd2d628940620'
ROUND='q0103-995b06ea'
GATE_SHA='67eb693bf07ec6e726c41ab67d5c6ff101412b0a1ca004a2e837c5b1dedf8341'
FAILURES=['HudStatus-panel-offscreen','MissionHud-panel-offscreen','MissionHud-panel-oversized',
          'RouteHud-panel-offscreen','RouteHud-panel-oversized','cache-rendered-base-not-grounded']

def validate_pause(old):
    expected=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=ROUND,
        task_index=7,task_failures=24,failure_streak=1,diagnosis_used=True,second_street_attempts=4,
        overall_deadline_epoch=HARD_CAP_EPOCH,saved_compact_hud_recovered=True,stage='native-chapter-presentation')
    if any(old.get(k)!=v for k,v in expected.items()) or old.get('presentation_measured_repair_attempted'):
        raise Halt('Require exact saved presentation candidate and preserved baseline/history')
    if not old.get('blocker','').startswith('Halt: Measured HUD/cache presentation requires correction:'):
        raise Halt('Do not mask a different failure')

def validate_failure(gate):
    check=gate.get('presentation_geometry',{})
    if not gate.get('passed') or gate.get('candidate_commit')!=SOURCE or check.get('passed') or check.get('failure')!=FAILURES:
        raise Halt('Preserve the actual chapter PASS and six presentation failures')
    ex=check.get('examples',[{}])[0];center=ex.get('cache_bounds_center',[]);size=ex.get('cache_bounds_size',[])
    if len(center)!=3 or len(size)!=3 or abs(center[1]-size[1]/2-.28)>.005:
        raise Halt('Cache duplicate-ground-offset diagnosis no longer matches measured bounds')

class MeasuredChapterLayout(ChapterPresentation):
    def validate_recovery(self,old):
        validate_pause(old);self.verify_prior()
        path=self.store.root/'evidence'/ROUND/'chapter-gate.json'
        if sha(path.read_bytes())!=GATE_SHA:raise Halt('Original native presentation evidence changed')
        validate_failure(read_json(path))

    def recovery_settings(self):
        return {**super().recovery_settings(),'presentation_measured_repair_attempted':True,
            'chapter_presentation_native_attempts':2,
            'recovery_change':'Keep live-window limits; also observe960x540capture projection. Local HUD bounds fit both; local cache offset removes second0.14m. Preserve original native failure.'}

    def source(self,ident):
        files=Files(self.project,self.store);raw=files.path(PATH).read_text()
        logic=raw[raw.index('        void Update()'):raw.index('        void ActivateCache()')]
        first=raw.index('        Transform missionHud;');last=raw.index('        void Update()')
        edit=SelectedEdit(files,PATH,raw.count('\n',0,first)+1,raw.count('\n',0,last),max_lines=170)
        def save(_,f):return edit.apply(ident+'-measured-hud',validate_visual_span(f['content'],max_lines=170))
        self.c.update(output_tokens=6144,model_timeout_seconds=320)
        self.store.set(stage='local-measured-hud-bounds');self.store.report()
        self.model.session('builder',ident+'-measured-hud',
            'You are local Qwen repairing only measured UI bounds in your saved visual code.',
            'The native chapter PASS is preserved. Your new HUD fits960x540 PNGs, but the live gameplay viewport '
            'is narrower: measured RouteHud cardX0.368..1.017, MissionHud-0.140..0.362, HudStatus-0.087..0.254. '
            'Keep the existing live-window checks AND the16:9capture view valid; do not change the camera, resolution '
            'or acceptance. Make only these layout corrections to the selected HUD region, preserving all text/state '
            'and other logic: RouteHud backing width1.40 instead of1.75 (keep height0.23); HudStatus active X-1.20 '
            'instead of-1.55; MissionHud active X-0.68 instead of-1.05. Keep their current Y/Z and scales. '
            'Additionally narrow the ORIGINAL MissionHud backing only while chapter active: localScale(1.20,0.24,0.01), '
            'localPosition(0,-0.075,0.025). This gives room for its unchanged R-to-reset third line. Cache that '
            'existing HudCard transform and its ORIGINAL localScale/localPosition when BuildHud finds MissionHud, '
            'then restore the exact cached values at stage0/R. Never hide the receipt or status. Do not change '
            'MissionHud font/text, actor/camera transforms, game progress, helper APIs, cache styling or Update. '
            'Preserve lazy HudStatus discovery, existing original-position/scale restoration, two-line objective '
            'and the restrained tintedMat behavior. Save the complete selected region in<=170lines/6000bytes '
            '(original is130lines/4650bytes). No unrelated rewrites.\nEXACT CURRENT REGION:\n'+edit.old,
            [tool('edit_selected_span','Save the measured UI-only replacement.',{'content':{'type':'string'}})],
            {'edit_selected_span':save},turns=1,reasoning_effort='low')
        if files.path(PATH).read_text()==raw:raise Halt('Measured HUD edit was not saved')
        candidate=self.checkpoint_source('Local Qwen: fit compact HUD to live and captured viewports')
        self.store.set(source_checkpoint=candidate,candidate_commit=candidate)
        raw=files.path(PATH).read_text()
        first=raw.index('                // World offset: center X/Z -> anchor X/Z, min Y -> anchor.y + 0.14')
        last=raw.index('                c.position += delta;',first)+len('                c.position += delta;')
        marker=SelectedEdit(files,PATH,raw.count('\n',0,first)+1,raw.count('\n',0,last)+1,max_lines=9)
        expected=marker.old.replace('anchor.y + 0.14','anchor.y').replace('(aPos.y + 0.14f)','aPos.y')
        def ground(_,f):
            if f['content'].strip()!=expected.strip():raise ValueError('Remove only the duplicate ground height and correct its comment')
            return marker.apply(ident+'-ground',f['content'])
        self.c.update(output_tokens=1536,model_timeout_seconds=120)
        self.store.set(stage='local-cache-ground-offset');self.store.report()
        self.model.session('builder',ident+'-ground',
            'You are local Qwen correcting one measured vertical offset.',
            'Actual cache rendered minimumY is0.28, but anchorY already equals pavement top0.14. '
            'Your expression adds0.14 twice. Replace (aPos.y + 0.14f) with aPos.y and change only the comment '
            'anchor.y + 0.14 to anchor.y. Preserve every other byte of the selected block.\n'+marker.old,
            [tool('edit_selected_span','Remove only the duplicated ground offset.',{'content':{'type':'string'}})],
            {'edit_selected_span':ground},turns=1,reasoning_effort='low')
        after=files.path(PATH).read_text()
        if after==raw:raise Halt('Local cache ground-offset correction was not saved')
        if after[after.index('        void Update()'):after.index('        void ActivateCache()')]!=logic:
            raise Halt('Gameplay Update changed outside this visual scope')
        candidate=self.checkpoint_source('Local Qwen: align cache base to the actual pavement once')
        self.store.set(source_checkpoint=candidate,candidate_commit=candidate);return candidate

if __name__=='__main__':raise SystemExit(main(MeasuredChapterLayout))
