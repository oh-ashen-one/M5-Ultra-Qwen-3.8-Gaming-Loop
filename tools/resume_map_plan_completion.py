#!/usr/bin/env python3
"""One focused completion after the map planner exhausted four read-only turns."""
from continue_game_queue import ContinuousRunner
from resume_three_day_queue import ThreeDayRunner, main
from resume_courier_qualification import NEXT_MAP
from qualify_map_extension import MAP_TASK, qualify_one_extension
from loop_controller.core import Files, Halt
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.model import tool
from loop_controller.runner import git

SOURCE='9062fb834071aa88fc374bce4181e48703a0f2ef'
ACCEPTED='d269dc43ac66c39afca4cb98ea53f9e7ed36806f'
ROUND='q0051-7f3ba74b'
BLOCKER='Halt: Map planner did not finish a bounded implementable design'
CONTEXT_FILES=('Assets/Game/Bootstrap.cs','Assets/Game/WorldColliders.cs',
               'Assets/Game/VehicleInteraction.cs','Assets/Game/Mission.cs')


def validate_plan_pause(old):
    expected=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=ROUND,
        task_index=7,task_failures=8,failure_streak=1,diagnosis_used=True,
        overall_deadline_epoch=HARD_CAP_EPOCH,blocker=BLOCKER,map_after_courier_attempted=True)
    if any(old.get(k)!=v for k,v in expected.items()) or old.get('map_plan_completion_attempted'):
        raise Halt('Expected exact map planner read-turn stop; preserve unrelated faults')
    if old.get('map_extension_plan') or old.get('accepted_map_extension'):
        raise Halt('A saved map plan or acceptance already exists')


class MapPlanCompletion(ThreeDayRunner):
    def validate_recovery(self,old):
        validate_plan_pause(old)
        if git(self.repo,'diff','--name-only',ACCEPTED,SOURCE,'--','game'):
            raise Halt('Plan completion requires the exact accepted fallback game')

    def recovery_settings(self):return {'map_plan_completion_attempted':True}

    def design(self,task,ident,diagnosis=False):
        if task['id']!=MAP_TASK['id'] or diagnosis:return super().design(task,ident,diagnosis)
        files=Files(self.project,self.store)
        source='\n\n'.join(path+'\n'+files.path(path).read_text() for path in CONTEXT_FILES)
        self.c.update(output_tokens=8192,model_timeout_seconds=400)
        self.store.event('complete-bounded-map-plan',original_session=ROUND+'-design',
            diagnosis='Four source-reading turns completed; no plan tool call; no source changes.',
            source_files=list(CONTEXT_FILES),original_failure_counts_preserved=True)
        result=self.model.session('planner',ident+'-plan-completion',
            'You are the sole local Qwen game designer. Finish one concise implementable plan using the exact source supplied.',
            'The prior bounded planner used all four turns on read_file and never submitted a plan. '
            'No game edits were made. Relevant current modules are now supplied in full; there are no read tools '
            'in this completion call. Assets/Resources/Generated/street/scene.prefab does not exist: Bootstrap '
            'already loads the existing generated street model. Use the actual shown API and existing art only. '
            'Return one submit_plan call now with a concise decision (maximum6500characters): connector placement '
            'that preserves the current forward/west collision tests, minimal files/edit sequence, physical '
            'walk/drive out-and-back route and corresponding normal-input replay. No implementation source in '
            'this plan; local builder follows. Do not replan the whole game, camera, courier or mission. '
            'Do not change or bypass old tests.\nBOUNDED TASK:\n'+task['instructions']+
            '\nEXACT CURRENT SOURCE:\n'+source,
            [tool('submit_plan','Finish one bounded map-extension implementation decision.',{'decision':{'type':'string'}})],
            {'submit_plan':lambda _,f:{'ok':True,'decision':f['decision'][:6500]}},
            turns=1,reasoning_effort='xhigh')
        if not result.get('ok'):raise Halt('Focused map plan completion did not submit; no automatic reattempt')
        self.store.set(task_design=result['decision'])
        return result

    def work(self):
        self.machine.guard()
        self.store.set(task_design=NEXT_MAP)
        qualify_one_extension(self)
        self.store.set(task_design=NEXT_MAP,
            feedback={'accepted_connector':self.store.get('accepted_map_extension'),
                      'next_required_milestone':NEXT_MAP})
        return ContinuousRunner.work(self)


if __name__=='__main__':raise SystemExit(main(MapPlanCompletion))
