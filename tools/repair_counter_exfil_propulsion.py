#!/usr/bin/env python3
"""Local correction of measured unbounded runner pushing and the Armed hint."""
from qualify_qwen_capacity import CapacityAuthor
from implement_counter_exfil import TASK,validate_source
from finish_counter_exfil_parts import RUNNER,MISSION,ACCEPTED
from submit_counter_exfil_parts import between,writes_shared_signals
from resume_three_day_queue import main
from loop_controller.core import Files,Halt,atomic,sha
from loop_controller.model import tool
from loop_controller.delivery_policy import HARD_CAP_EPOCH

SOURCE='9df6c96af1ccd25d3115a44434a23aec0537d273'
PRIOR='q0176-57452fa8'

def validate_boundary(old):
    expected=dict(status='paused',controller_pid=None,owned_process=None,current_round=PRIOR,
        source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,task_index=7,task_failures=24,
        failure_streak=1,diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,
        blocker='Halt: Counter-Exfil physical success attempt recorded; independent contact, shot and crossing proof required')
    result=old.get('counter_exfil_success_outcome',{})
    if (any(old.get(k)!=v for k,v in expected.items()) or old.get('counter_exfil_propulsion_repair_attempted')
            or result.get('candidate')!=SOURCE or not result.get('native',{}).get('passed')
            or result.get('reported_completion_time') is not None or result.get('reported_failure_time') is None):
        raise Halt('Require the measured real success-route failure and unchanged source/history')

class RepairCounterPropulsion(CapacityAuthor):
    source_context_tokens=65536
    source_output_tokens=16384
    def validate_recovery(self,old):
        validate_boundary(old);self.prior=old['counter_exfil_source_outcome']
        self.resume_capacity=self.priority_resume=self.transport_recovery=self.admission_recovery=False
    def recovery_settings(self):
        return dict(counter_exfil_propulsion_repair_attempted=True,recovery_route='local-measured-finite-runner-propulsion',
            recovery_change='Actual unoccupied coupe is pushed west about1.1m/s by the velocity-forced runner, defeating genuine foot-exit pins. Locally bound physical propulsion while retaining dynamic collisions, gravity, release and free escape; shorten the unchanged41character Armed hint. Camera/aim route is an external-input correction, not gameplay editing.')
    def work(self):
        ident=self.begin(TASK,'local-counter-exfil-physical-propulsion-repair');files=Files(self.project,self.store)
        originals={p:files.path(p).read_text() for p in (RUNNER,MISSION)}
        mission=originals[MISSION]
        spawn=between(mission,'        void SpawnOne(','        void RecordEscape(')
        hint=between(mission,'        public string HudLine','        public string Objective')
        protected={str(p.relative_to(self.project)):sha(p.read_bytes()) for p in self.project.rglob('*')
            if p.is_file() and p.suffix in ('.cs','.shader','.fbx','.blend','.py') and str(p.relative_to(self.project)) not in originals}
        def save(action,fields):
            runner=fields['runner_source'];new_spawn=fields['spawn_method'];new_hint=fields['hint_property']
            for content,limit,lines in [(runner,24000,340),(new_spawn,7000,100),(new_hint,1400,25)]:
                if not isinstance(content,str) or len(content.encode())>limit or len(content.splitlines())>lines:
                    raise ValueError('Return complete bounded selected source only')
                if writes_shared_signals(content):raise ValueError('Never write shared health, input, score or old chapter signals')
                validate_source(RUNNER,content)
            runner=runner.rstrip()+'\n';new_spawn=new_spawn.rstrip()+'\n';new_hint=new_hint.rstrip()+'\n'
            if not new_spawn.lstrip().startswith('void SpawnOne(') or not new_hint.lstrip().startswith('public string HudLine'):
                raise ValueError('Return exactly the supplied mission method and property')
            if runner==originals[RUNNER] or new_hint.strip()==hint.strip():raise ValueError('Save the actual propulsion and compact-hint corrections')
            updated=mission.replace(spawn,new_spawn,1).replace(hint,new_hint,1)
            files.edit(action+'-runner',RUNNER,sha(originals[RUNNER].encode()),old=originals[RUNNER],new=runner)
            files.edit(action+'-mission',MISSION,sha(mission.encode()),old=mission,new=updated)
            if any(sha(files.path(p).read_bytes())!=h for p,h in protected.items()):raise Halt('Protected gameplay, camera, HUD or assets changed')
            candidate=self.checkpoint_source('Local Qwen: bound physical runner propulsion and compact the Armed hint')
            self.store.set(source_checkpoint=candidate);self.store.report()
            return dict(ok=True,local_authored=True,candidate=candidate,changed_files=[RUNNER,MISSION],native_verified=False)
        self.c.update(working_context_tokens=self.source_context_tokens,output_tokens=self.source_output_tokens,model_timeout_seconds=600)
        result=self.model.session('builder',ident+'-propulsion-source',
            'You are local Qwen, sole gameplay author. Save a focused correction from the measured native failure.',
            'MEASURED: the real1200kg coupe was driven west and parked across the lane at(9.553,-.01,17.827), '
            'yaw1.393degrees. With the driver still seated, lead contact genuinely qualified around102s. '
            'When ordinary E exits at100.2s, your80kg lead pushes the unoccupied coupe fromX9.553 at100.33 '
            'toX6.215 at105.43 andX2.336 at109.03; lead real west speed is about1.1m/s, hold stays0, '
            'and it genuinely escapes at109.233. All actors remain dynamic and collision is real. '
            'PhysicsStep overwrites horizontal velocity with DriveSpeed every fixed step, injecting '
            'unbounded momentum into contact chains. Fix physical propulsion so real car obstruction '
            'can persist after the living player exits; account for following runners pushing through '
            'the lead as well. Use finite force/acceleration that respects mass, ground friction and '
            'collisions, with actual forward motion still effective on unobstructed ground. If needed, '
            'set a sensible physical material only on these NEW runner capsules in SpawnOne. The existing '
            'coupe has mass1200,drag.6,static/dynamic friction.05,Minimum combine; runner mass80,drag0, '
            'default capsule friction; all unchanged world colliders stay. Do not modify the car, world '
            'or old actors. No frozen/kinematic live pins, position clamps, cached resolution, disabled '
            'colliders, parent attachment, hidden state writes or fake stops. Preserve genuine contact '
            'plus measured obstruction for continuous.8s, immediate contact-loss clearing, death gates, '
            'actual free westbound escape,6/3/3HP, existing public API and exact surveyed lane. '
            'The full success replay also fired9misses because its0.1s A press turns only54degrees; '
            'that is a declared cloud input-authoring error, fixed separately. DO NOT edit camera, aim '
            'or combat. Second correction: your unchanged Armed hint at20m is41characters. Return '
            'a genuinely shorter single line <=40characters for0..999m, retaining coupe distance and '
            'E/F actions. Keep all four old ending lines and the already-fixed backing untouched. '
            'Return COMPLETE CounterExfilRunner.cs, exact complete SpawnOne method (unchanged if '
            'material adjustment unnecessary) and exact complete HudLine property. No extra features, '
            'planning or expanded commentary. Native physical/negative/old-route/pixel checks remain '
            'required.\nCURRENT RUNNER:\n'+originals[RUNNER]+'\nEXACT SPAWN METHOD:\n'+spawn+
            '\nEXACT HINT PROPERTY:\n'+hint,
            [tool('finish_source','Save actual complete runner plus only the selected spawn and hint spans.',
                {'runner_source':{'type':'string'},'spawn_method':{'type':'string'},'hint_property':{'type':'string'}})],
            {'finish_source':save},turns=3,reasoning_effort='xhigh',
            retained_assistant=getattr(self,'retained_author',None),retained_instruction=getattr(self,'retained_instruction',None))
        atomic(self.store.root/'evidence'/(ident+'-propulsion-source.json'),result)
        if not result.get('ok'):raise Halt('Preserve actual runner propulsion failure and local source; focused repair incomplete')
        self.store.set(counter_exfil_propulsion_result=result,counter_exfil_source_outcome=dict(self.prior,candidate=result['candidate'],propulsion_repair=result));self.store.report()
        raise Halt('Local Counter-Exfil finite propulsion saved; unload idle inference and requalify real physics and presentation')

if __name__=='__main__':raise SystemExit(main(RepairCounterPropulsion))
