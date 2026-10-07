#!/usr/bin/env python3
"""Local presentation repair after ten regression passes and a real visual FIX."""
import json
from resume_three_day_queue import main
from resume_map_traversal import MapTraversalRecovery,ACCEPTED
from qualify_map_extension import MAP_TASK
from loop_controller.core import Files,Halt
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.model import tool
from loop_controller.recovery_policy import replay_identity
from loop_controller.runner import git
from loop_controller.small_edits import SelectedEdit

SOURCE='edec84f9ab3c30a3a4c1e364999a0ca615214957'
CANDIDATE='d526046537d456bb224a247e88d190157286e2d2'
ROUND='q0070-1baf81f6'
REPLAY='43879c58b005b9b888e3be11fd0fed8ea5652487937bca44d21b9d10908d91b9'
PATH='Assets/Game/WorldColliders.cs'


def validate_presentation_pause(old):
    expected=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=ROUND,
        task_index=7,task_failures=16,failure_streak=1,diagnosis_used=True,
        overall_deadline_epoch=HARD_CAP_EPOCH,vehicle_contact_fix_submitted=True,
        blocker='Halt: Repeated diagnosed blocker on connected-map-extension; failed source preserved and last playable state restored')
    if any(old.get(k)!=v for k,v in expected.items()) or old.get('alley_presentation_recovery_attempted'):
        raise Halt('Expected exact preserved full-native PASS followed by local visual FIX')
    if replay_identity(old['last_valid_replay'])!=REPLAY:
        raise Halt('Keep the physically proven map input sequence')


class AlleyPresentation(MapTraversalRecovery):
    def validate_recovery(self,old):
        validate_presentation_pause(old)
        p=self.store.root/'evidence'/ROUND
        gate=json.loads((p/'scoped-gate.json').read_text());review=json.loads((p/'critic.json').read_text())
        checks=gate.get('regressions',{}).get('regressions',[])
        if (gate.get('candidate_commit')!=CANDIDATE or not gate.get('passed')
                or len(checks)!=10 or not all(x['gate'].get('passed') for x in checks)
                or not review.get('ok') or review.get('verdict')!='FIX'):
            raise Halt('Require all actual physical/regression passes and the independent visual rejection')
        if git(self.repo,'diff','--name-only',ACCEPTED,SOURCE,'--','game'):
            raise Halt('Preserve accepted fallback before restoring the proven local candidate')

    def recovery_settings(self):
        return dict(alley_presentation_recovery_attempted=True,recovery_route='local-presentation-repair',
            recovery_change='Match street material, reveal existing entrance, add original mesh alley boundaries',
            presentation_native_budget=1)

    def selected(self,ident,label,needle,instruction,max_lines):
        files=Files(self.project,self.store);path=files.path(PATH);raw=path.read_text()
        found=[i+1 for i,line in enumerate(raw.splitlines()) if line.strip()==needle]
        if len(found)!=1:raise Halt('Expected one complete '+label+' insertion line')
        edit=SelectedEdit(files,PATH,found[0],found[0],max_lines=max_lines)
        self.c.update(output_tokens=4096,model_timeout_seconds=210)
        self.store.set(stage='local-alley-'+label);self.store.report()
        self.model.session('builder',ident+'-'+label,
            'You are the sole local Qwen author. Make only the selected small C# edit and save immediately.',
            instruction+'\nEXACT OLD LINE:\n'+edit.old+'\nACTUAL SOURCE CONTEXT:\n'+raw,
            [tool('edit_selected_span','Save this bounded original mesh/presentation change.',{'content':{'type':'string'}})],
            {'edit_selected_span':lambda action,f:edit.apply(action,f['content'])},turns=1,reasoning_effort='low')
        if path.read_text()==raw:
            self.report_blocker('Local alley '+label+' submitted no saved edit',ident)
            raise Halt('Scoped alley presentation edit not submitted; physics candidate preserved')
        saved=self.checkpoint_source('Local Qwen: alley '+label)
        self.store.set(source_checkpoint=saved,candidate_commit=saved)

    def prepare_source(self):
        if git(self.repo,'rev-parse','HEAD')!=SOURCE:raise Halt('One exact visual repair only')
        git(self.repo,'restore','--source='+CANDIDATE,'--','game')
        saved=self.checkpoint_source('Recover physically qualified local map for visual alley repair')
        self.store.set(source_checkpoint=saved)

    def edit(self,task,ident):
        if task['id']!=MAP_TASK['id']:return super().edit(task,ident)
        self.prepare_source()
        self.selected(ident,'matching-asphalt','ap.AddComponent<MeshRenderer>().sharedMaterial = omr.sharedMaterial;',
            'The local visual critic rejects the tan slab as disconnected from the grey street. Replace only '
            'this material assignment: obtain the existing active scene GameObject named road_asphalt, '
            'read its MeshRenderer.sharedMaterial, and assign it to the new ap MeshRenderer; if absent '
            'fall back to omr.sharedMaterial. Declare all local variables; no new material or asset. '
            'Preserve pavement mesh, pivot, thickness, colliders, geometry, actors and replay. At most5lines.',5)
        self.selected(ident,'visible-entrance','// 3) Understandable end barriers using the original fence mesh.',
            'Before this exact comment, hide ONLY the original decorative fence mesh pieces that visually '
            'cross the existing physical opening at world X5..6,Z8..20, then preserve the comment. '
            'Iterate the supplied roots (Object[] containing GameObjects or Components, as already handled '
            'above), and their MeshRenderers whose name starts fence_. For pieces with bounds.center.x '
            'between5and6 and bounds.center.z between8and20, set only renderer.enabled=false. '
            'Native scene verified those original Props/fence_run pieces have no Collider; do not disable '
            'or remove ANY collider, actor, pier, bin, wall, or other renderers. Keep original fence outside '
            'the opening intact. This reveals the existing usable junction; it changes no route. At most14lines.',14)
        self.selected(ident,'visible-alley-walls','// 3) Understandable end barriers using the original fence mesh.',
            'The critic needs visible bounded alley scenery, not a bare plane. Insert three walls using '
            'only the existing original facade_wall MeshFilter.sharedMesh and MeshRenderer.sharedMaterial; '
            'then preserve this comment. Find the existing scene object named facade_wall. It has imported '
            'basis localX->worldZ, localY->worldX, localZ->worldY. Its actual world bounds are '
            '8m thickX,8.8m highY,12m longZ; use mesh.bounds sizes/center, not guessed origin. '
            'Create AlleySouthWall and AlleyNorthWall with world target bounds size(16,8.8,0.5), '
            'centers(14,4.4,7.75) and(14,4.4,20.25). Their rotation is worldY90degrees times the '
            'source rotation; localScale=(16/b.size.x,0.5/b.size.y,8.8/b.size.z). '
            'Create AlleyEndWall with world size(0.5,8.8,12), center(22.25,4.4,14), source rotation, '
            'localScale=(12/b.size.x,0.5/b.size.y,8.8/b.size.z). For each mesh, offset position by '
            'rotation*Vector3.Scale(b.center,localScale) so its actual bounds center matches the target. '
            'Parent each to go; reuse the source mesh/material; add a BoxCollider with the same local '
            'mesh bounds. These footprints coincide with existing outer physical barriers, so keep all '
            'current barriers and the X6 opening unchanged. No obstacles inside X6..22,Z8..20, no added '
            'art files/assets, no new gameplay, no camera/input/mission/vehicle edits. At most36lines. '
            'Use declared arrays/local variables or a short loop; do not introduce an undefined helper.',36)
        scenario=self.store.get('last_valid_replay')
        if replay_identity(scenario)!=REPLAY:raise Halt('Native map replay changed during visual repair')
        self.store.event('local-alley-presentation-saved',candidate=self.store.get('source_checkpoint'),
            prior_native_candidate=CANDIDATE,unchanged_replay=True,prior_visual_verdict='FIX',
            fresh_native_and_ten_regressions_required=True,cloud_game_code_authored=False)
        return dict(ok=True,scenario=scenario)


if __name__=='__main__':raise SystemExit(main(AlleyPresentation))
