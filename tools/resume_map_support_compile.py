#!/usr/bin/env python3
"""Repair one undefined collider reference; replay the unexecuted third strategy."""
import json
from resume_three_day_queue import main
from resume_map_traversal import MapTraversalRecovery, ACCEPTED
from resume_map_support import PATH
from qualify_map_extension import MAP_TASK
from loop_controller.core import Files, Halt
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.model import tool
from loop_controller.recovery_policy import replay_identity
from loop_controller.runner import git
from loop_controller.small_edits import SelectedEdit

SOURCE='e838c4286ba3964d6893ea51e1e47f16e162ca51'
FAILED='bde6b7aa98fc786eded1dd890ce5186254f28fff'
ROUND='q0066-e93808ed'
REPLAY='43879c58b005b9b888e3be11fd0fed8ea5652487937bca44d21b9d10908d91b9'


def validate_compile_pause(old):
    expected=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=ROUND,
        task_index=7,task_failures=14,failure_streak=1,diagnosis_used=True,
        overall_deadline_epoch=HARD_CAP_EPOCH,map_support_repair_attempted=True,
        blocker='Halt: Repeated diagnosed blocker on connected-map-extension; failed source preserved and last playable state restored')
    if any(old.get(k)!=v for k,v in expected.items()) or old.get('map_support_compile_attempted'):
        raise Halt('Expected exact preserved undefined-collider compilation failure')
    history=old.get('map_traversal_strategies',[])
    if len(history)!=3 or history[-1].get('round')!=ROUND or replay_identity(old['last_valid_replay'])!=REPLAY:
        raise Halt('Preserve the three strategies and exact never-executed third replay')


class MapSupportCompile(MapTraversalRecovery):
    def validate_recovery(self,old):
        validate_compile_pause(old)
        gate=json.loads((self.store.root/'evidence'/ROUND/'scoped-gate.json').read_text())
        if gate.get('candidate_commit')!=FAILED or gate.get('failure')!='compile-build' or gate.get('player_exit') is not None:
            raise Halt('Compilation repair cannot reuse a previously executed strategy as unexecuted')
        errors=gate.get('compile_errors',[])
        if not errors or any("'_collider' does not exist" not in e and e!='Scripts have compiler errors.' for e in errors):
            raise Halt('Expected only the exact missing collider symbol')
        if git(self.repo,'diff','--name-only',ACCEPTED,SOURCE,'--','game'):
            raise Halt('Accepted fallback tree changed')

    def recovery_settings(self):
        return dict(map_support_compile_attempted=True,recovery_route='changed-strategy',
            recovery_change='One local collider-reference correction; preserve and execute the third saved strategy')

    def edit(self,task,ident):
        if task['id']!=MAP_TASK['id']:return super().edit(task,ident)
        if git(self.repo,'rev-parse','HEAD')!=SOURCE:raise Halt('Single exact compiler recovery only')
        git(self.repo,'restore','--source='+FAILED,'--','game')
        saved=self.checkpoint_source('Recover local support candidate for exact compiler correction')
        self.store.set(source_checkpoint=saved)
        files=Files(self.project,self.store);path=files.path(PATH);raw=path.read_text()
        indices=[i+1 for i,line in enumerate(raw.splitlines()) if 'float colliderBottomY =' in line]
        if len(indices)!=1:raise Halt('Expected one collider-bottom definition')
        edit=SelectedEdit(files,PATH,indices[0],indices[0],max_lines=2)
        self.c.update(output_tokens=1024,model_timeout_seconds=90)
        self.store.set(stage='local-collider-reference-repair');self.store.report()
        self.model.session('builder',ident+'-collider-reference',
            'Make the one-line C# compiler correction and immediately call edit_selected_span.',
            'The actual VehicleInteraction class has no _collider field. Native compile failed CS0103 '
            'at this exact line. The vehicle already has its BoxCollider on this same GameObject. '
            'Replace only the definition of colliderBottomY with the world-space minimum Y of that '
            'existing Collider, obtained via GetComponent<Collider>().bounds.min.y. Use no new field '
            'or helper; preserve the rest of the ground-support block. One line only. Exact old line:\n'+edit.old,
            [tool('edit_selected_span','Submit the single corrected collider-bottom definition.',
                  {'content':{'type':'string'}})],
            {'edit_selected_span':lambda action,f:edit.apply(action,f['content'])},turns=1,reasoning_effort='low')
        if path.read_text()==raw:
            self.report_blocker('One-line collider compiler correction was not submitted',ident)
            raise Halt('Collider reference correction not submitted; preserved source remains unaccepted')
        saved=self.checkpoint_source('Local Qwen: use actual Collider bounds for ground support')
        scenario=self.store.get('last_valid_replay')
        if replay_identity(scenario)!=REPLAY:raise Halt('Saved unexecuted third strategy changed')
        self.store.set(source_checkpoint=saved,candidate_commit=saved)
        self.store.event('compiler-only-map-strategy-requalification',candidate=saved,
            saved_strategy_round=ROUND,replay_sha256=REPLAY,native_strategy_count=3,
            counters_preserved=True,new_route_budget_granted=False,native_pass_claimed=False)
        return dict(ok=True,scenario=scenario)


if __name__=='__main__':raise SystemExit(main(MapSupportCompile))
