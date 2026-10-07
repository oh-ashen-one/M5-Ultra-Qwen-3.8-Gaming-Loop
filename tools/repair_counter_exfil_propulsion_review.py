#!/usr/bin/env python3
"""Local correction of two concrete reviewed propulsion integration defects."""
from qualify_qwen_capacity import CapacityAuthor
from repair_counter_exfil_propulsion import TASK,RUNNER,MISSION,ACCEPTED
from submit_counter_exfil_parts import between,writes_shared_signals
from implement_counter_exfil import validate_source
from resume_three_day_queue import main
from loop_controller.core import Files,Halt,atomic,sha
from loop_controller.model import tool
from loop_controller.delivery_policy import HARD_CAP_EPOCH

SOURCE='aa992c7f775b4a68b33fadc57688719fffe5937b'
PRIOR='q0179-2480df3e'

class RepairCounterPropulsionReview(CapacityAuthor):
    def validate_recovery(self,old):
        expected=dict(status='paused',controller_pid=None,owned_process=None,current_round=PRIOR,
            source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,task_index=7,task_failures=24,
            failure_streak=1,diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,
            counter_exfil_propulsion_final_recovered=True,
            blocker='Halt: Local Counter-Exfil finite propulsion saved; unload idle inference and requalify real physics and presentation')
        if (any(old.get(k)!=v for k,v in expected.items()) or old.get('counter_exfil_propulsion_review_attempted')
                or old.get('counter_exfil_propulsion_result',{}).get('candidate')!=SOURCE):
            raise Halt('Require exact recovered local propulsion source and unchanged stopped history')
        self.prior=old['counter_exfil_source_outcome']
        self.resume_capacity=self.priority_resume=self.transport_recovery=self.admission_recovery=False
    def recovery_settings(self):
        return dict(counter_exfil_propulsion_review_attempted=True,recovery_route='local-propulsion-api-and-terminal-stop-correction',
            recovery_change='Fix two reviewed integration defects through local authorship: installed Unity uses PhysicsMaterial APIs; terminal StopDrive disables future PhysicsStep, so a flag alone cannot stop the body. Preserve bounded active propulsion, dynamic living colliders, original source and native requirements.')
    def work(self):
        ident=self.begin(TASK,'local-counter-exfil-propulsion-review');files=Files(self.project,self.store)
        originals={p:files.path(p).read_text() for p in (RUNNER,MISSION)}
        selected={RUNNER:between(originals[RUNNER],'        /// <summary>Cancel commanded forward drive.','        void OnCollisionEnter('),
            MISSION:between(originals[MISSION],'        void SpawnOne(','        void RecordEscape(')}
        protected={str(p.relative_to(self.project)):sha(p.read_bytes()) for p in self.project.rglob('*')
            if p.is_file() and p.suffix in ('.cs','.shader','.fbx','.blend','.py') and str(p.relative_to(self.project)) not in originals}
        def save(action,fields):
            replacements={RUNNER:fields['stop_method'],MISSION:fields['spawn_method']}
            for path,value in replacements.items():
                if not isinstance(value,str) or len(value.encode())>7000 or len(value.splitlines())>100:
                    raise ValueError('Return only two complete bounded selected source spans')
                value=value.rstrip()+'\n';replacements[path]=value
                if value.strip()==selected[path].strip():raise ValueError('Both concrete defects require correction')
                validate_source(path,value)
                if writes_shared_signals(value):raise ValueError('Never write shared gameplay signals')
            for path,value in replacements.items():
                files.edit(action+'-'+path.rsplit('/',1)[-1],path,sha(originals[path].encode()),old=selected[path],new=value)
            if any(sha(files.path(p).read_bytes())!=h for p,h in protected.items()):raise Halt('Protected source changed')
            candidate=self.checkpoint_source('Local Qwen: use installed material API and stop terminal runner motion')
            self.store.set(source_checkpoint=candidate);self.store.report()
            return dict(ok=True,local_authored=True,candidate=candidate,changed_files=[RUNNER,MISSION],native_verified=False)
        self.c.update(working_context_tokens=65536,output_tokens=8192,model_timeout_seconds=600)
        result=self.model.session('builder',ident+'-propulsion-review-source',
            'You are local Qwen, sole gameplay author. Save exactly the two small reviewed source corrections through finish_source.',
            'Your complete finite-force runner and compact Armed hint are saved. Two concrete integration fixes '
            'remain. (1) The installed Unity6.5 project already uses PhysicsMaterial and PhysicsMaterialCombine '
            '(note Physics, not Physic) in VehicleInteraction.cs. Correct the obsolete names only in the '
            'selected SpawnOne method; preserve all values and other behavior. (2) CounterExfilMission.StopDrive '
            'sets driving=false and calls each CoastToStop; FixedUpdate calls PhysicsStep only while driving. '
            'Therefore setting stopRequested=true cannot execute future bounded braking. In this terminal/death '
            'method only, stop existing horizontal body motion once while preserving Y/gravity, dynamic living '
            'body and solid collider. Keep stopRequested for consistency. This is invoked only after death, '
            'failure or completion; it must not create live obstruction credit. Do not change active finite '
            'propulsion, qualification/contact logic, car/world, camera, aim, HP, chapter or HUD. Return selected '
            'complete stop method with its corrected short comment and selected complete SpawnOne. No extra '
            'planning/comments. Native verification follows.\nSTOP SPAN:\n'+selected[RUNNER]+'\nSPAWN SPAN:\n'+selected[MISSION],
            [tool('finish_source','Save the two complete selected C# spans.',
                {'stop_method':{'type':'string'},'spawn_method':{'type':'string'}})],{'finish_source':save},
            turns=3,reasoning_effort='xhigh')
        atomic(self.store.root/'evidence'/(ident+'-propulsion-review.json'),result)
        if not result.get('ok'):raise Halt('Preserve local propulsion source; focused API/terminal-stop correction incomplete')
        self.store.set(counter_exfil_propulsion_review_result=result,
            counter_exfil_source_outcome=dict(self.prior,candidate=result['candidate'],propulsion_review=result));self.store.report()
        raise Halt('Reviewed local Counter-Exfil propulsion saved; unload idle inference and qualify actual incident')

if __name__=='__main__':raise SystemExit(main(RepairCounterPropulsionReview))
