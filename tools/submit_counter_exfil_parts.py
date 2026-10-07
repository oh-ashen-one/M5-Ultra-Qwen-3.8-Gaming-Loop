#!/usr/bin/env python3
"""Submit concrete local source directly, avoiding repeated read/edit bookkeeping."""
import re
from qualify_qwen_capacity import CapacityAuthor
from implement_counter_exfil import TASK,HUD,NEW,validate_source
from finish_counter_exfil_parts import MISSION,RUNNER,DEATH,ACCEPTED
from resume_three_day_queue import main
from loop_controller.core import Files,Halt,atomic,sha
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.model import tool

SOURCE='94fa1d766ae5efa95ed5ec843b51fbcb78e3da1d'
PRIOR='q0165-5a43eb63'

def validate_boundary(old):
    expected=dict(status='paused',controller_pid=None,owned_process=None,current_round=PRIOR,
        source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,task_index=7,task_failures=24,
        failure_streak=1,diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,
        counter_exfil_parts_attempted=True,counter_exfil_current_part='crossing',
        blocker='Halt: Preserve usable local Counter-Exfil saves; complete source submission needs focused continuation')
    if (any(old.get(k)!=v for k,v in expected.items()) or old.get('counter_exfil_direct_submission_attempted')
            or old.get('counter_exfil_source_outcome',{}).get('bounded_stop')!='turns'):
        raise Halt('Require the exact saved-source tool-turn boundary and unchanged accepted history')

def between(source,start,end):
    a=source.index(start);b=source.index(end,a);return source[a:b]

def writes_shared_signals(source):
    return bool(re.search(r'LoopSignals\.(Health|Restarts|Shots|Hits|Mode|Mission)\s*(?:[+*/-]?=(?!=)|\+\+|--)',source))

class SubmitCounterExfil(CapacityAuthor):
    part_labels=('crossing','runner','hud')
    source_context_tokens=65536
    source_output_tokens=16384
    def validate_recovery(self,old):
        validate_boundary(old)
        self.resume_capacity=self.priority_resume=self.transport_recovery=self.admission_recovery=False
    def recovery_settings(self):
        return dict(counter_exfil_direct_submission_attempted=True,recovery_route='direct-local-source-submissions',
            recovery_change='Preserve all saved source and bounded history. Supply the complete exact current '
            'file and a single terminal source-save tool per focused part, eliminating repeated read/replace '
            'bookkeeping. Same local model/xhigh and original guards. Native acceptance remains independent.')
    def work(self):
        ident=self.begin(TASK,'local-counter-exfil-direct-source')
        files=Files(self.project,self.store);parts=list(getattr(self,'initial_parts',[]))
        tasks=[('crossing',MISSION,
            'The saved SampleFoot still sets crossedWest whenever Settled, without requiring footEastOfExit '
            'or an actual crossing. Replace ONLY that exact method. Capture the PREVIOUS foot position '
            'before overwriting lastFoot. Require consecutive valid living foot samples, bounded actual '
            'walking displacement, previous X strictly east and current X west of EXIT_X, central Z band '
            'and Settled at the crossing. Standing already west, an E exit across the line, or crossing '
            'while unresolved then waiting west must never complete. Clear stale crossing on invalid '
            'samples/vehicle/death; preserve normal east re-arming. Existing Update calls SampleFoot every '
            'active frame and Cleanup/Begin call ClearCrossing. Use those actual fields/methods. '
            'Return one complete SampleFoot method, at most80lines/6000bytes. No other changes.'),
          ('runner',RUNNER,
            'Return the COMPLETE current CounterExfilRunner.cs with only two focused fixes: '
            '(1) OnCollisionExit from the actual coupe immediately clears lastContact and hold. Re-entry '
            'requires a fresh continuous0.8seconds; no0.12-second separation credit. Pinned is false '
            'immediately when DeathAuthority.IsDead. Preserve genuine contact plus measured obstruction '
            'and dynamic living bodies. (2) LaneZ follows the actual piecewise survey: LaneEast '
            '47.605/17.4603 ->22/16.5738 ->6/16.0057 ->LaneWest3/16.0057, preserving the current '
            'public API. Leave other behavior intact. No new features or commentary expansion. '
            'Return complete C# source, at most300lines/20000bytes.'),
          ('hud',HUD,
            'Return COMPLETE MissionDirectorHud.cs with only chapter installation and board integration. '
            'Call CounterExfilMission.Install(player,cam) once from the existing Install method. '
            'Use its actual Armed/BoardPriority/Objective/HudLine/FailReason API supplied below. '
            'While Armed preserve the old interception ending and append its one compact HudLine. '
            'When BoardPriority is true show the new actual Objective. Death retains the existing exact '
            'health-depleted text/colour and R guidance, preserving a genuine specific CounterExfil '
            'failure reason ahead of the death notice when present. Keep all old chapter fallbacks, '
            'Setup, sizes, materials, Courier, ParseCd, signal access, camera and reticle unchanged. '
            'No planning or extra features. Return complete C# source, at most350lines/24000bytes.')]
        for label,path,instruction in tasks:
            if label not in self.part_labels:continue
            self.store.set(counter_exfil_current_part=label);self.store.report()
            original=files.path(path).read_text();digest=sha(original.encode())
            protected={str(p.relative_to(self.project)):sha(p.read_bytes()) for p in self.project.rglob('*')
                if p.is_file() and p.suffix in ('.cs','.shader','.fbx','.blend','.py') and p!=files.path(path)}
            selected=between(original,'        void SampleFoot()','        void ClearCrossing()') if label=='crossing' else original
            extra=files.path(DEATH).read_text() if label=='runner' else files.path(MISSION).read_text() if label=='hud' else ''
            def submit(action,fields):
                content=fields['content']
                limit,lines=(6000,80) if label=='crossing' else (20000,300) if label=='runner' else (24000,350)
                if not isinstance(content,str) or len(content.encode())>limit or len(content.splitlines())>lines:
                    raise ValueError('Return only the complete selected source within the stated size bound')
                if not content.endswith('\n'):content+='\n'
                if label=='crossing' and not content.lstrip().startswith('void SampleFoot()'):
                    raise ValueError('Return only the exact SampleFoot method replacement')
                updated=original.replace(selected,content,1) if label=='crossing' else content
                if label=='hud':
                    accessor=original[original.index('        static string ReadStr('):]
                    if (accessor not in updated or between(original,'        void Setup()','        void LateUpdate()') not in updated
                            or between(original,'        string Courier(','        T FindAny<') not in updated):
                        raise ValueError('Preserve exact Setup, Courier/ParseCd and legacy signal accessor')
                    validate_source(path,updated.replace('using System.Reflection;','').replace(accessor,''))
                else:validate_source(path,updated)
                if writes_shared_signals(updated):
                    raise ValueError('The chapter cannot write shared health, combat, mode or old mission signals')
                if updated==original:raise ValueError('Save the actual requested change')
                result=files.edit(action,path,digest,old=selected,new=content)
                if any(sha(files.path(p).read_bytes())!=h for p,h in protected.items()):
                    raise Halt('Direct local source save changed a protected file')
                candidate=self.checkpoint_source('Local Qwen: finish Counter-Exfil '+label)
                self.store.set(source_checkpoint=candidate);self.store.report()
                return dict(ok=True,local_authored=True,part=label,candidate=candidate,changed_files=[path],
                    source_sha256=sha(files.path(path).read_bytes()),native_verified=False)
            self.c.update(working_context_tokens=self.source_context_tokens,output_tokens=self.source_output_tokens,model_timeout_seconds=600)
            result=self.model.session('builder',ident+'-'+label+'-source',
                'You are local Qwen, sole gameplay author. Submit actual finished C# through finish_source now.',
                instruction+'\nAll source below is exact current text and hash-backed. No read calls or '
                'additional planning are needed. A successful finish_source both saves the code and ends '
                'this focused part. Do not merely claim completion.\nCURRENT FILE:\n'+original+
                '\nEXACT SELECTED SOURCE TO REPLACE:\n'+selected+'\nREAD-ONLY DEPENDENCY:\n'+extra,
                [tool('finish_source','Save the actual complete selected C# source and finish this part.',{'content':{'type':'string'}})],
                {'finish_source':submit},turns=3,reasoning_effort='xhigh',
                retained_assistant=getattr(self,'retained_parts',{}).get(label),
                retained_instruction=getattr(self,'retained_instruction',None) if label in getattr(self,'retained_parts',{}) else None)
            atomic(self.store.root/'evidence'/(ident+'-'+label+'-source.json'),result)
            if not result.get('ok'):raise Halt('Preserve saved local source; direct '+label+' submission incomplete: '+str(result.get('bounded_stop','no source tool')))
            parts.append(result);self.store.set(counter_exfil_direct_parts=parts);self.store.report()
        outcome=dict(ok=True,local_authored=True,candidate=self.store.get('source_checkpoint'),
            changed_files=sorted(NEW|{HUD}),parts=parts,native_verified=False,final_game_accepted=False)
        atomic(self.store.root/'evidence'/(ident+'-counter-exfil-author.json'),outcome)
        self.store.set(counter_exfil_source_outcome=outcome);self.store.report()
        raise Halt('Local Counter-Exfil source saved; unload idle inference and qualify actual inputs and negatives')

if __name__=='__main__':raise SystemExit(main(SubmitCounterExfil))
