#!/usr/bin/env python3
"""Finish bounded critique, then local world-transform and compact wall-detail edits."""
import json
from continue_game_queue import ContinuousRunner, review_captures
from resume_three_day_queue import main
from resume_alley_readability import AlleyReadability, PATH, NEEDLE
from resume_map_traversal import ACCEPTED, BLOCKER
from resume_alley_presentation import REPLAY
from qualify_map_extension import MAP_TASK
from loop_controller.core import Files, Halt, atomic, sha, verify_seal
from loop_controller.delivery_policy import HARD_CAP_EPOCH, queue_milestone
from loop_controller.model import tool
from loop_controller.prop_clone_checks import inspect_alley_clones
from loop_controller.recovery_policy import replay_identity
from loop_controller.runner import git
from loop_controller.small_edits import SelectedEdit

SOURCE='38241b76a38ca4c88f4e44158fee4d6dea445d06'
CANDIDATE='8439ae8789793a881c51003cad94e39fc7210c01'
ROUND='q0074-fe18ab28'


def validate_prop_pause(old):
    expected=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=ROUND,
        task_index=7,task_failures=18,failure_streak=1,diagnosis_used=True,
        overall_deadline_epoch=HARD_CAP_EPOCH,alley_saved_visuals_attempted=True,blocker=BLOCKER)
    if any(old.get(k)!=v for k,v in expected.items()) or old.get('alley_prop_transforms_attempted'):
        raise Halt('Expected the exact preserved fresh-critic context stop')
    if replay_identity(old['last_valid_replay'])!=REPLAY:raise Halt('Preserve physical inputs')


class PropTransforms(AlleyReadability):
    def validate_recovery(self,old):
        validate_prop_pause(old)
        bundle=self.store.root/'evidence'/ROUND
        gate=json.loads((bundle/'scoped-gate.json').read_text())
        review=json.loads((bundle/'critic.json').read_text())
        checks=gate.get('regressions',{}).get('regressions',[])
        if (gate.get('candidate_commit')!=CANDIDATE or not gate.get('passed') or len(checks)!=10
                or not all(x['gate'].get('passed') for x in checks) or review.get('bounded_stop')!='context'):
            raise Halt('Require all ten native passes and original no-verdict context stop')
        if git(self.repo,'diff','--name-only',ACCEPTED,SOURCE,'--','game'):
            raise Halt('Preserve accepted fallback')
        objects=json.loads((bundle/'captures/scene-transforms.json').read_text())['objects']
        if inspect_alley_clones(objects)['passed']:raise Halt('Repair requires measured clone mismatch')

    def recovery_settings(self):
        return dict(alley_prop_transforms_attempted=True,recovery_route='local-prop-world-transform-repair',
            recovery_change='Bounded original critique, exact local world-transform fix, two small door details',
            prop_transform_native_budget=1)

    def repair_transforms(self,ident):
        files=Files(self.project,self.store);path=files.path(PATH);raw=path.read_text()
        needle='inst.transform.SetParent(go.transform, true);'
        matches=[i+1 for i,line in enumerate(raw.splitlines()) if line.strip()==needle]
        if len(matches)!=1:raise Halt('Expected one exact clone-parenting line')
        edit=SelectedEdit(files,PATH,matches[0],matches[0],max_lines=6)
        self.c.update(output_tokens=2048,model_timeout_seconds=120)
        self.store.set(stage='local-prop-world-transform-repair');self.store.report()
        self.model.session('builder',ident+'-prop-transforms',
            'You are the sole local game author. Submit this small evidenced transform fix immediately.',
            'Native scene bounds prove the new prop clones lost imported parent transforms: source world '
            'scale100 became1 and source upright axes were lost. Preserve this parenting line, then '
            'copy srcs[i].transform.rotation to inst.transform.rotation and source lossyScale to '
            'inst.transform.localScale. The go parent is an identity transform. Do this BEFORE the '
            'existing Renderer.bounds aggregation and floor translation. Preserve targets, original '
            'props, existing colliders and all other code. At most4lines.\nOLD:\n'+edit.old+
            '\nEXACT CURRENT SOURCE:\n'+raw,
            [tool('edit_selected_span','Save only this clone world-transform repair.',{'content':{'type':'string'}})],
            {'edit_selected_span':lambda action,f:edit.apply(action,f['content'])},turns=1,reasoning_effort='low')
        if path.read_text()==raw:raise Halt('Local prop-transform repair not saved')
        saved=self.checkpoint_source('Local Qwen: preserve cloned prop world scale and orientation')
        self.store.set(source_checkpoint=saved,candidate_commit=saved)

    def complete_prior_review(self,task,ident):
        bundle=self.store.root/'evidence'/ROUND
        # Preserve the original no-inference stop before completing its actual
        # independent review with a bounded, state-relevant image selection.
        original=bundle/'critic.json';archive=bundle/'critic-context-stop.json'
        if archive.exists():raise Halt('Original critic stop already archived')
        archive.write_bytes(original.read_bytes())
        manifest_hash=sha((bundle/'captures/manifest.json').read_bytes())
        verify_seal(bundle/'captures',manifest_hash)
        gate=json.loads((bundle/'scoped-gate.json').read_text())
        objects=json.loads((bundle/'captures/scene-transforms.json').read_text())['objects']
        observed=inspect_alley_clones(objects)
        gate['scoped_facts']['observed_prop_transform_defect']={
            'passed':observed['passed'],'failure':observed['failure'],
            'meaning':'Native original/clone world size and orientation mismatch; not a failure of the passing traversal.'}
        review=ContinuousRunner.review(self,task,ident+'-prior-lighting-review',bundle,gate)
        verify_seal(bundle/'captures',manifest_hash)
        if not review.get('ok') or review.get('verdict') not in ('PASS','FIX'):
            raise Halt('Bounded lighting review did not supply a verdict')
        self.store.event('prior-lighting-review-completed',prior_round=ROUND,review=review,
            original_context_stop_preserved=True,measured_clone_defect_still_requires_repair=True)

    def edit(self,task,ident):
        if task['id']!=MAP_TASK['id']:return super().edit(task,ident)
        if git(self.repo,'rev-parse','HEAD')!=SOURCE:raise Halt('Expected preserved fallback before local repair')
        self.complete_prior_review(task,ident)
        git(self.repo,'restore','--source='+CANDIDATE,'--','game')
        saved=self.checkpoint_source('Recover local lighting and props for measured transform correction')
        self.store.set(source_checkpoint=saved)
        self.repair_transforms(ident)
        # One original mesh per request avoids the earlier combined-detail
        # output exhaustion. The existing solid wall remains authoritative.
        for label,source in [('service-panel','door00_panel'),('service-surround','door00_surround')]:
            self.selected(ident,label,
                'Add exactly ONE closed service-door mesh from the existing scene object named '+source+'. '
                'Find that object, get its MeshFilter/sharedMesh and MeshRenderer/sharedMaterial. '
                'Create one empty GameObject under go and copy those mesh/material references. '
                'Set localScale to source.transform.lossyScale; set rotation to worldY90degrees times '
                'source.transform.rotation so it faces world-Z into the alley. After assigning mesh, '
                'scale and rotation, use the NEW MeshRenderer.bounds to translate the object until its '
                'horizontal center is worldX16,Z19.92 and its bottomY is0.14. This is one closed '
                'decorative part on the north solid wall, not a new passage. No loop, helper, collider, '
                'script or unrelated change. Use a brace-scoped local block and at most14lines.',24)
        scenario=self.store.get('last_valid_replay')
        if replay_identity(scenario)!=REPLAY:raise Halt('Preserve the complete physical replay')
        self.store.event('local-prop-transform-and-wall-detail-saved',candidate=self.store.get('source_checkpoint'),
            physical_inputs_unchanged=True,cloud_game_code_authored=False)
        return dict(ok=True,scenario=scenario)

    def native(self,task,ident,candidate,probe):
        bundle,gate=ContinuousRunner.native(self,task,ident,candidate,probe)
        if task['id']==MAP_TASK['id'] and gate.get('passed'):
            objects=json.loads((bundle/'captures/scene-transforms.json').read_text())['objects']
            check=inspect_alley_clones(objects)
            gate['scoped_facts']['prop_clone_parity']=check
            if not check['passed']:gate.update(passed=False,failure=check['failure'])
            atomic(bundle/'scoped-gate.json',gate)
        if gate.get('passed') and 'regression' not in ident:
            frames,times=review_captures(task,bundle)
            queue_milestone(self.store,'native-milestone',task,bundle,gate,frames,times)
        return bundle,gate


if __name__=='__main__':raise SystemExit(main(PropTransforms))
