#!/usr/bin/env python3
"""Focused local repairs and paired native combat tests; no generic planning round."""
import json
import uuid

from inspect_combat_contracts import SOURCE,ACCEPTED
from recover_mission_replay import block_span
from loop_controller.core import Files,Halt,atomic,read_json,sha
from loop_controller.continuous_tasks import TASKS
from loop_controller.combat_checks import FOOT_PROBE,WALL_PROBE,DRIVE_PROBE,inspect_combat_contract
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.model import tool
from loop_controller.small_edits import SelectedEdit
from resume_mission_review import verified_probe
from resume_three_day_queue import ThreeDayRunner,main

COMBAT='Assets/Game/Combat.cs'
VISUAL_REPAIRED='ed84a51d044d67735dfc7c4af18651d4c943f9a5'


def combined_probe(previous):
    offset=16.5
    return dict(id='combat-and-accepted-courier',coverage='combat',duration=38,
        steps=FOOT_PROBE['steps']+[dict(start=offset,end=offset+.3,keys=['R'])]+[
            {**s,'start':s['start']+offset,'end':s['end']+offset} for s in previous['steps']],
        captures=[3.2,6.9,8,10,17.2,24.4,26.2,29,31.7,35])


class CombatFocus(ThreeDayRunner):
    def validate_recovery(self,old):
        initial=(old.get('source_checkpoint')==SOURCE and old.get('blocker')==
                 'Halt: Combat diagnostic complete; preserve source for measured small local fixes')
        selected_stop=(old.get('source_checkpoint')==VISUAL_REPAIRED and old.get('blocker')==
            'Halt: Local combat edit saved no change: chase-and-occluded-attack' and
            old.get('combat_selected_edits')==['preserve-imported-visual-basis','rival-pavement-height'] and
            {v.get('scope') for v in old.get('combat_before_contracts',[])}=={'foot','wall'})
        if (old.get('task_index')!=4 or not (initial or selected_stop)
                or old.get('last_playable_checkpoint')!=ACCEPTED or old.get('task_failures')!=0
                or old.get('failure_streak')!=0 or old.get('overall_deadline_epoch')!=HARD_CAP_EPOCH):
            raise Halt('Expected the preserved measured combat diagnostic and accepted retry baseline')

    def recovery_settings(self):return {'combat_focused_qualification_pending':True}

    def native_test(self,ident,probe,kind,candidate):
        bundle=self.store.root/'evidence'/ident
        self.store.set(stage='native-combat-'+kind,combat_probe=ident);self.store.report()
        gate=self.engines.unity(self.project,bundle,probe,candidate)
        if not gate.get('passed'):raise Halt('Combat diagnostic runtime failed: '+str(gate.get('failure')))
        rows=[json.loads(x) for x in (bundle/'captures/trace.jsonl').read_text().splitlines()]
        result=inspect_combat_contract(rows,kind)
        result.update(candidate=candidate,build_id=gate['build_id'],evidence=str(bundle.relative_to(self.store.root)),
                      acceptance_fixture=probe.get('fixture'))
        atomic(bundle/'combat-contract.json',result)
        self.store.event('combat-contract-observed',**result)
        return result

    def selected(self,ident,label,instruction,method=None,start=None,end=None,max_lines=50):
        if label in self.store.get('combat_selected_edits',[]):return
        files=Files(self.project,self.store);source=files.path(COMBAT).read_text();lines=source.splitlines()
        if method:a,z=block_span(source,method)
        else:
            starts=[i+1 for i,l in enumerate(lines) if start in l];ends=[i+1 for i,l in enumerate(lines) if end in l]
            if len(starts)!=1 or len(ends)!=1:raise Halt('Expected one exact combat span: '+label)
            a,z=starts[0],ends[0]
        edit=SelectedEdit(files,COMBAT,a,z,max_lines=max_lines)
        self.c.update(output_tokens=4096,model_timeout_seconds=240)
        self.store.set(stage='selected-combat-edit',combat_microtask=label);self.store.report()
        self.model.session('builder',ident+'-'+label,
            'You are local Qwen, the sole game-code author. Save one exact selected source replacement now.',
            instruction+' Keep the replacement compact, at most '+str(max_lines)+' lines. Preserve unrelated behavior. '
            'No replay detection or fake telemetry. Use existing Set(string,object), ReadStr(string), ReadInt(string). '
            'LoopSignals.Player and Vehicle are Transform; Mode is the string foot or vehicle. '
            'Only your returned source bytes will be saved.\nCURRENT FIELD/API CONTEXT:\n'+'\n'.join(lines[:65])+
            '\nEXACT SELECTED SOURCE:\n'+edit.old,
            [tool('edit_selected_span','Replace only this exact read-backed source span.',{'content':{'type':'string'}})],
            {'edit_selected_span':lambda action,f:edit.apply(action,f['content'])},turns=1,reasoning_effort='low')
        if sha(files.path(COMBAT).read_bytes())==edit.before:raise Halt('Local combat edit saved no change: '+label)
        candidate=self.checkpoint_source('Local Qwen: combat '+label)
        self.store.set(source_checkpoint=candidate,combat_selected_edits=self.store.get('combat_selected_edits',[])+[label])
        self.store.event('selected-combat-edit-saved',microtask=label,candidate=candidate,game_author='local Qwen')

    def work(self):
        if not self.store.get('combat_focused_qualification_pending'):raise Halt('Focused qualification is one-time only')
        ident='combat-focus-'+uuid.uuid4().hex[:8]
        before=self.store.get('combat_before_contracts') or [
            self.native_test(ident+'-before-'+kind,probe,kind,SOURCE)
            for kind,probe in [('foot',FOOT_PROBE),('wall',WALL_PROBE)]]
        self.store.set(combat_before_contracts=before)
        self.selected(ident,'preserve-imported-visual-basis',
            'Native evidence: imported rival renders only0.0157m tall initially, then0.004m tall while turning, '
            'although its capsule is1.9m. Fix only instantiation: create a new unit-scale identity-rotation GameObject '
            'wrapper named Rival in go. Instantiate the existing Generated/player/scene as its visual CHILD, preserving '
            'the imported child rotation and scale exactly. The accepted player uses this same imported visual with '
            'a local Y offset of-0.79m; apply that offset to the child. Put the wrapper at RIVAL_SPAWN only after '
            'parenting the visual. All later collider and RivalAgent code must remain on the unit wrapper go. '
            'Do not set the imported child localScale or localRotation to identity. Keep a simple capsule fallback '
            'only if the existing prefab is missing; no new asset generation.',
            start='var prefab = Resources.Load<GameObject>',end='go.transform.localScale = Vector3.one;',max_lines=18)
        self.selected(ident,'rival-pavement-height',
            'Keep the same X2,Z-0.5 spawn and name. Set only its Y to0.14f, the measured visible pavement top, '
            'so the wrapper and imported visual feet stand on the same surface as the player.',
            start='static readonly Vector3 RIVAL_SPAWN =',end='static readonly Vector3 RIVAL_SPAWN =',max_lines=2)
        self.selected(ident,'chase-and-occluded-attack',
            'The previous proposal was rejected unchanged:70 lines exceeded65. Return ONLY the compact ActRival '
            'method, with target resolution and ordered collision check inline; no extra helper methods or long comments. '
            'Measured defect: while driving22.7m from the rival, health continues falling every1.6s because the inactive '
            'foot player remains3m away. Resolve the actual controlled Transform each update: use LoopSignals.Vehicle '
            'when Mode is vehicle and it exists; otherwise player. Chase, range and tracer endpoint must all use that '
            'same target. Preserve speeds, cooldown, damage and HP behavior. Before damage, cast from the rival muzzle '
            'to the target body, ignore only the rival own hierarchy, and use the nearest remaining non-trigger physical '
            'collision. A nearer world wall must prevent damage and tracer penetration; allow damage only if the first '
            'collision belongs to the controlled target or no obstacle lies before its body point. Sort RaycastAll by '
            'distance if using it; never discard world hits to seek the actor beyond. Preserve ordinary visible chase.',
            method='void ActRival()',max_lines=65)
        self.selected(ident,'actual-actor-pursuit',
            'Use the same actual controlled actor rule as ActRival: Vehicle while Mode is vehicle and present, else '
            'player. Measure real actor-to-rival distance for every pursuit tier. Keep the existing5/10/18m thresholds, '
            'encounter/alive conditions and real derived signal. Do not clear pursuit merely from entering a car.',
            method='void UpdatePursuit()',max_lines=25)
        self.selected(ident,'nearest-world-hit-occludes-fire',
            'Fix the proven static defect where RaycastAll discards nearer walls. For the existing camera-forward '
            'shot, select the nearest physical non-trigger hit after ignoring only the shooter own player hierarchy '
            'and actual controlled vehicle hierarchy while driving. World collisions must stop the shot before a rival. '
            'Only if that FIRST collider belongs to a live RivalAgent may its HP and Hits change. The tracer must end '
            'at that first collision. Preserve real Mouse0 input, Shots count, HP/death/flash behavior, range and cooldown '
            'semantics. No layer, wall, target-size or hit-radius shortcuts.',method='void HandleFire()',max_lines=65)
        candidate=self.checkpoint_source('Local Qwen: measured combat repairs')
        self.store.set(source_checkpoint=candidate)
        after=[self.native_test(ident+'-after-'+kind,probe,kind,candidate)
               for kind,probe in [('foot',FOOT_PROBE),('wall',WALL_PROBE),('driving',DRIVE_PROBE)]]
        atomic(self.store.root/'combat-focused-result.json',{'before':before,'after':after,'candidate':candidate})
        self.store.set(combat_after_contracts=after,combat_focused_qualification_pending=False)
        if not all(v['passed'] for v in after):
            self.reject_scoped(TASKS[4],ident,{'failure':[f for v in after for f in (v.get('failure') or [])]},candidate)
            raise Halt('Measured combat contract failure; preserve candidate and diagnose exact observations')
        prior,_=verified_probe(self.store.root,TASKS[4]);probe=combined_probe(prior)
        task=TASKS[4];bundle,gate=self.native(task,ident+'-combined',candidate,probe)
        if gate.get('passed'):
            regression=self.regress(task,ident+'-combined',candidate);gate['regressions']=regression
            if not regression['passed']:gate.update(passed=False,failure=regression['failure'])
            atomic(bundle/'scoped-gate.json',gate)
        if not gate.get('passed'):
            self.reject_scoped(task,ident,gate,candidate)
            raise Halt('Combined combat/courier or accepted baseline regression failed; inspect exact native evidence')
        review=self.review(task,ident+'-combined',bundle,gate)
        if not review.get('ok') or review.get('verdict')!='PASS':
            self.reject_scoped(task,ident,review,candidate)
            raise Halt('Scoped combat review did not pass; preserve bounded diagnosis')
        self.promote(task,candidate,bundle,gate,review)
        return super().work()


if __name__=='__main__':raise SystemExit(main(CombatFocus))
