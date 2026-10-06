#!/usr/bin/env python3
"""Repair the controller-selected incomplete lookup span through the local author."""
from continue_game_queue import ContinuousRunner
from resume_three_day_queue import main
from resume_map_spans import MapSpanBuilder,PATH
from resume_pavement_completion import pavement_lookup_span
from resume_map_replay_case import saved_replay,SESSION
from resume_courier_qualification import NEXT_MAP
from qualify_map_extension import MAP_TASK,qualify_one_extension
from loop_controller.core import Halt
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.runner import git

SOURCE='7318149f58fc37291911cd287c0f2f4068531e74'
FAILED='4918935c9989b942b4dff908dcc9dce6e376a584'
ACCEPTED='d269dc43ac66c39afca4cb98ea53f9e7ed36806f'
ROUND='q0056-e358262a'
BLOCKER='Halt: Repeated diagnosed blocker on connected-map-extension; failed source preserved and last playable state restored'


def validate_compile_pause(old):
    expected=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=ROUND,
        task_index=7,task_failures=9,failure_streak=1,diagnosis_used=True,
        overall_deadline_epoch=HARD_CAP_EPOCH,blocker=BLOCKER,map_replay_case_recovery_attempted=True)
    if any(old.get(k)!=v for k,v in expected.items()) or old.get('map_compile_recovery_attempted'):
        raise Halt('Expected exact preserved map compile rejection')


class MapCompileRecovery(MapSpanBuilder):
    def validate_recovery(self,old):
        validate_compile_pause(old)
        if git(self.repo,'diff','--name-only',ACCEPTED,SOURCE,'--','game'):
            raise Halt('Expected exact accepted fallback before recovering failed local source')
        saved_replay((self.store.root/'private/sessions'/SESSION/'response-001.json').read_bytes())

    def recovery_settings(self):return {'map_compile_recovery_attempted':True}

    def edit(self,task,ident):
        if task['id']!=MAP_TASK['id']:return super().edit(task,ident)
        if git(self.repo,'rev-parse','HEAD')!=SOURCE:raise Halt('One compile repair only')
        git(self.repo,'restore','--source='+FAILED,'--','game/'+PATH)
        original=self.checkpoint_source('Recover rejected local map source for exact lookup repair')
        self.store.set(source_checkpoint=original)
        self.store.event('restore-original-local-candidate-for-repair',failed_candidate=FAILED,
            reason='Controller matched an inline condition and truncated the lookup replacement span',
            cloud_game_code_authored=False,accepted_checkpoint_unchanged=True)
        raw=(self.project/PATH).read_text();first,last=pavement_lookup_span(raw)
        self.span(ident,'complete-pavement-lookup',first,last,
            'The controller previously supplied an incomplete lookup span. That left an orphaned FindDeep(g...) '
            'line with break and an unmatched closing brace, causing native compiler errors. Replace this '
            'entire selected span with at most4lines: safely find the existing scene-root GameObject named '
            'Pavement and assign Transform pv0 or null. Do not keep any old foreach tail. The following '
            'whole-line if(pv0!=null) and its body are outside the span and must remain intact. Preserve all '
            'geometry, materials, colliders and other game behavior. Call edit_selected_span now.',raw,4)
        result=saved_replay((self.store.root/'private/sessions'/SESSION/'response-001.json').read_bytes())
        self.store.set(last_valid_replay=result['scenario'])
        self.store.event('reuse-local-map-replay-after-compile-repair',source_session=SESSION,
            timings_unchanged=True,native_pass_claimed=False)
        return result

    def work(self):
        self.machine.guard();self.store.set(task_design=NEXT_MAP)
        qualify_one_extension(self,integrated_builder=True)
        self.store.set(task_design=NEXT_MAP,
            feedback={'accepted_connector':self.store.get('accepted_map_extension'),'next_required_milestone':NEXT_MAP})
        return ContinuousRunner.work(self)


if __name__=='__main__':raise SystemExit(main(MapCompileRecovery))
