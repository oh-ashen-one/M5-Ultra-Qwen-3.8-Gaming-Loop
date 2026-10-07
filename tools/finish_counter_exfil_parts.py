#!/usr/bin/env python3
"""Complete the saved incident using three small local source contexts."""
from implement_counter_exfil import ImplementCounterExfil,SOURCE as ACCEPTED,HUD,NEW
from resume_three_day_queue import main
from loop_controller.core import Halt,atomic
from loop_controller.delivery_policy import HARD_CAP_EPOCH

SOURCE='afcd00df54c616bcc2c497083652117038bb4cd0'
PRIOR='q0164-ecbd3182'
MISSION='Assets/Game/CounterExfilMission.cs'
RUNNER='Assets/Game/CounterExfilRunner.cs'
DEATH='Assets/Game/DeathAuthority.cs'
PARTS=(
 ('crossing',MISSION,{MISSION,RUNNER,DEATH},
  'ONLY finish the saved mission crossing now. The previous context saved the compiler-placeholder fix, '
  'HudLine and proposed crossing fields, but FootAtWestExit is STILL only a position test and Cleanup '
  'does not clear the added fields. Implement a real consecutive living on-foot east-to-west crossing '
  'of the validated central exit; sample while Active even when not yet settled, clear crossing history '
  'on vehicle/death/R, and require all three killed or currently pinned AT that crossing. Standing '
  'beyond the line before resolution and E-exiting a car across the line must not count. Keep the exit '
  'region supported by the actual central native corridor, not an invented wide side lane. Keep all '
  'other behavior/source intact. Do not rewrite comments or add features. Save code then finish_task '
  'for this one file; separate local contexts finish runner and HUD next.'),
 ('runner',RUNNER,{RUNNER,DEATH},
  'ONLY finish the saved runner now. Add immediate real coupe collision-exit handling that clears both '
  'the current contact and the uninterrupted hold. Re-entry starts a fresh0.8-second qualification; '
  'the old0.12-second contact freshness allowance must not carry credit across an actual separation. '
  'Pinned must be false immediately when DeathAuthority.IsDead. Keep actual collision, measured '
  'obstruction and dynamic physical movement; no cached or frozen living pins. Also make LaneZ use '
  'the exact surveyed piecewise path: existing LaneEast47.605/17.4603, middle22/16.5738, '
  'middle6/16.0057, existing LaneWest3/16.0057. Do this within the existing runner API; the mission '
  'already supplies LaneEast/West. No other files or features. Save code then finish_task for this file.'),
 ('hud',HUD,{HUD,MISSION,DEATH},
  'ONLY finish installation/HUD now. CounterExfilMission and CounterExfilRunner already exist; the '
  'previous two focused contexts finished their physical/crossing fixes. Add exactly one '
  'CounterExfilMission.Install(player,cam) call through the existing MissionDirectorHud.Install. '
  'Read its public Armed/BoardPriority/Objective/HudLine/FailReason API. Keep the old interception '
  'ending visible while Armed, appending its ONE compact HudLine, not two full boards. Active or '
  'terminal new state shows its actual Objective. Death always keeps the exact existing health-depleted '
  'text/colour, with the new chapter specific genuine failure reason preserved if one exists. '
  'Preserve old death behavior and all old chapter fallbacks, camera, reticle, sizing and materials. '
  'Read exact current spans after each edit. Save the real integration, then finish_task. No planning.')
)

def validate_boundary(old):
    expected=dict(status='paused',controller_pid=None,owned_process=None,current_round=PRIOR,
        source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,task_index=7,task_failures=24,
        failure_streak=1,diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,
        counter_exfil_finish_source_attempted=True,
        blocker='Halt: Preserve usable local Counter-Exfil saves; complete source submission needs focused continuation')
    if (any(old.get(k)!=v for k,v in expected.items()) or old.get('counter_exfil_parts_attempted')
            or old.get('counter_exfil_source_outcome',{}).get('bounded_stop')!='context'):
        raise Halt('Require saved mission edits and the exact context stop; preserve old playable source/history')

class CounterExfilParts(ImplementCounterExfil):
    author_context_tokens=65536
    author_output_tokens=16384
    def validate_recovery(self,old):
        validate_boundary(old);self.survey=old['counter_exfil_preflight']
        self.resume_capacity=self.priority_resume=self.transport_recovery=self.admission_recovery=False
    def recovery_settings(self):
        return dict(counter_exfil_parts_attempted=True,recovery_route='small-counter-exfil-code-contexts',
            recovery_change='Preserve useful saved mission edits. Finish crossing, runner contact/lane and '
            'HUD installation in three fresh smaller exact-source contexts, one writable file each. '
            'No broad planning, model restart, quality reduction, failure reset or acceptance change.')
    def work(self):
        self.completed_parts=[]
        for label,path,context,instruction in PARTS:
            self.part=label;self.context_files=context;self.writable_paths={path};self.must_change={path}
            self.focused_instruction='CURRENT PHASE OVERRIDES THE GENERAL WHOLE-INCIDENT BRIEF: '+instruction
            self.store.set(counter_exfil_current_part=label);self.store.report()
            super().work()
    def finish_author(self,ident,result):
        if not result.get('ok'):
            result['incomplete_part']=self.part
            return super().finish_author(ident,result)
        self.completed_parts.append(dict(part=self.part,**result))
        atomic(self.store.root/'evidence'/(ident+'-counter-exfil-'+self.part+'.json'),result)
        self.store.set(counter_exfil_completed_parts=self.completed_parts);self.store.report()
        if self.part=='hud':
            result.update(changed_files=sorted(NEW|{HUD}),phases=self.completed_parts)
            super().finish_author(ident,result)

if __name__=='__main__':raise SystemExit(main(CounterExfilParts))
