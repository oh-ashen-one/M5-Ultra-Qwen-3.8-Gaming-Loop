#!/usr/bin/env python3
"""Two exact local-authored source spans after the whole-module output-limit stop."""
from continue_game_queue import ContinuousRunner
from resume_three_day_queue import ThreeDayRunner, main
from resume_direct_map_builder import DirectMapBuilder
from resume_courier_qualification import NEXT_MAP
from qualify_map_extension import MAP_TASK, qualify_one_extension
from loop_controller.core import Files,Halt
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.model import tool
from loop_controller.runner import git
from loop_controller.small_edits import SelectedEdit

SOURCE='9062fb834071aa88fc374bce4181e48703a0f2ef'
ACCEPTED='d269dc43ac66c39afca4cb98ea53f9e7ed36806f'
ROUND='q0053-a5e1326b'
BLOCKER='Halt: Direct map author saved no module; no automatic reattempt'
PATH='Assets/Game/WorldColliders.cs'


def validate_span_pause(old):
    expected=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=ROUND,
        task_index=7,task_failures=8,failure_streak=1,diagnosis_used=True,
        overall_deadline_epoch=HARD_CAP_EPOCH,blocker=BLOCKER,map_direct_builder_attempted=True)
    if any(old.get(k)!=v for k,v in expected.items()) or old.get('map_span_builder_attempted'):
        raise Halt('Expected exact preserved whole-module output-limit stop')


class MapSpanBuilder(ThreeDayRunner):
    def validate_recovery(self,old):
        validate_span_pause(old)
        if git(self.repo,'diff','--name-only',ACCEPTED,SOURCE,'--','game'):
            raise Halt('Small map spans require exact accepted fallback')
        if (self.project/'Assets/Game/MapExtension.cs').exists():
            raise Halt('Preserve an existing module rather than switching approaches over it')

    def recovery_settings(self):return {'map_span_builder_attempted':True}

    def span(self,ident,label,first,last,instructions,context,max_lines):
        files=Files(self.project,self.store);path=files.path(PATH);before=path.read_text()
        edit=SelectedEdit(files,PATH,first,last,max_lines=max_lines)
        self.c.update(output_tokens=8192,model_timeout_seconds=400)
        self.store.set(stage='local-map-'+label);self.store.report()
        self.model.session('builder',ident+'-'+label,
            'You are the sole local Qwen game coder. Make only the supplied small exact edit and call the tool now.',
            instructions+'\nEXACT OLD SPAN:\n'+edit.old+'\nREAD-ONLY SOURCE CONTEXT:\n'+context,
            [tool('edit_selected_span','Save only this bounded original C# source replacement.',{'content':{'type':'string'}})],
            {'edit_selected_span':lambda action,f:edit.apply(action,f['content'])},
            turns=1,reasoning_effort='low')
        if path.read_text()==before:raise Halt('Small map '+label+' edit saved no change')
        saved=self.checkpoint_source('Local Qwen: map '+label)
        self.store.set(source_checkpoint=saved,candidate_commit=saved)

    def edit(self,task,ident):
        if task['id']!=MAP_TASK['id']:return super().edit(task,ident)
        files=Files(self.project,self.store);raw=files.path(PATH).read_text();lines=raw.splitlines()
        first=next(i+1 for i,line in enumerate(lines) if 'AddWall(go, new Vector3(PX1 + WALL_T' in line)
        self.span(ident,'side-opening',first,first+1,
            'Replace just this east boundary wall with two AddWall calls preserving X center6.25, thickness0.5 '
            'and existing WALL_H. The retained wall segments cover Z-2..8 and Z20..30, leaving a12m-wide east '
            'opening Z8..20. Keep all other walls and major-object colliders unchanged. Compute each segment '
            'center/length directly; at most6lines. No other source, planning essay, helper, scene or replay.',
            raw[:raw.index('        static bool IsMajor')],6)
        raw=files.path(PATH).read_text();lines=raw.splitlines()
        first=next(i+1 for i,line in enumerate(lines) if '// 3) Understandable end barriers' in line)
        bootstrap=files.path('Assets/Game/Bootstrap.cs').read_text()
        paving=bootstrap[bootstrap.index('            Transform sw = null;'):bootstrap.index('            static GameObject Coupe()')]
        self.span(ident,'connected-pavement',first,first,
            'Before the existing section3 comment, add only a compact connected east pavement patch and its '
            'outer boundaries, then preserve that comment. Target rendered patch X6..22,Z8..20, topY0.14. '
            'Reuse the existing original Pavement MeshFilter mesh and MeshRenderer material, rotation/basis '
            'and vertical thickness. Its current world bounds are X-1..6,Z-2..30; imported local X maps to '
            'world Z, local Y maps to world X, local Z maps to world Y. Calculate the new local scale from '
            'the old dimensions and desired12m depth/16m width; position via the mesh local bounds center '
            'and rotated scaled center, not guessed pivot offset. Name it AlleyPavement. Give it a correctly '
            'aligned physical floor at the same visible surface. Bound east X22 and both Z8/Z20 edges across '
            'X6..22 with this existing AddWall helper. Reuse the existing original fence mesh via PlaceFence '
            'to make those three new barriers visible. Do not close the west connection at X6, overlap the '
            'old corridor with new obstacles, move original actors/props, alter existing controls or use '
            'invisible ground as a rendered map. Use only variables/helpers present here and UnityEngine. '
            'At most45lines/6000bytes; one edit_selected_span now, no separate planning or new module.',
            'EXISTING PAVEMENT CREATION:\n'+paving+'\nCURRENT WORLD COLLISION FILE:\n'+raw,45)
        return self.propose_replay(task,ident)

    def propose_replay(self,task,ident):
        if task['id']!=MAP_TASK['id']:return super().propose_replay(task,ident)
        # Reuse the bounded map-only replay contract without a nonexistent new module.
        files=Files(self.project,self.store)
        from loop_controller.replay_contract import finish_tool,validate_submission
        source='\n\n'.join(p+'\n'+files.path(p).read_text() for p in
            (PATH,'Assets/Game/VehicleInteraction.cs'))
        source+='\nBOOTSTRAP/WALKER:\n'+files.path('Assets/Game/Bootstrap.cs').read_text().split('    public class Follow')[0]
        self.c.update(output_tokens=8192,model_timeout_seconds=400)
        self.store.set(stage='local-map-replay');self.store.report()
        result=self.model.session('replay-author',ident+'-map-replay',
            'You are local Qwen proposing actual normal-input traversal, not changing source. Submit finish_task now.',
            'Use summary, duration, input_steps, captures. Each input step is {start,end,keys}; times fromlaunch, '
            'first4seconds stationary, duration16..150s, at least4 increasing captures before end. E presses '
            'last>=0.25s. The new east connection is X6,Z8..20, with visible floor toX22. First WALK across '
            'the connection toX>=12 (6m beyond old bound), remain>=1s, capture and physically walk back '
            'toX<=6. Then approach the actual car, E enter, DRIVE across toX>=12, remain>=1s, capture and '
            'physically drive back toX<=6; reversing is allowed. Use actual steering/throttle and walking '
            'speeds from source. No R teleports; no parcel mission required. Include captures of each outside '
            'mode and each return. Plan around actual existing props and piers; preserve collision, camera, '
            'mission and actors. A proposal is unverified until native execution.\nEXACT CURRENT SOURCE:\n'+source,
            [finish_tool()],{'finish_task':lambda _,f:validate_submission(f,task)},
            turns=2,reasoning_effort='low')
        if not result.get('scenario'):raise Halt('Small-span map replay not submitted; saved source preserved')
        self.store.set(last_valid_replay=result['scenario'])
        self.store.event('map-replay-preflight',duration=result['scenario']['duration'],native_pass_claimed=False)
        return result

    def work(self):
        self.machine.guard()
        self.store.set(task_design=NEXT_MAP)
        self.store.event('smaller-map-source-actions',prior_round=ROUND,
            original_output_stop_preserved=True,cloud_role='bounded task geometry and edit infrastructure',
            game_code_author='local Qwen',original_failure_counts_preserved=True)
        qualify_one_extension(self,integrated_builder=True)
        self.store.set(task_design=NEXT_MAP,
            feedback={'accepted_connector':self.store.get('accepted_map_extension'),
                      'next_required_milestone':NEXT_MAP})
        return ContinuousRunner.work(self)


if __name__=='__main__':raise SystemExit(main(MapSpanBuilder))
