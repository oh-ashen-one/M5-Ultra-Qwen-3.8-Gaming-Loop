#!/usr/bin/env python3
"""One useful local death-install/walking edit qualifies opt-in capacity accounting."""
from resume_player_death_focused import FocusedDeath
from resume_camera_native_only import ACCEPTED
from resume_three_day_queue import main
from loop_controller.core import Halt, atomic, read_json
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from qwen_capacity import Budget, POLICY

SOURCE='ac0d7fe441a48377eb8d3bb420da2618ed797ed6'


def validate_boundary(old):
    expected=dict(status='paused',controller_pid=None,owned_process=None,current_round='q0144-dd98c86e',
        source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,task_index=7,task_failures=24,
        failure_streak=1,diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,
        shared_workload_priority='simultaneous-no-default-priority',capacity_trial_runtime_attempted=True,
        blocker='Halt: Capacity trial stopped during model load: compressor-growth-above2GiB; no author request started')
    if (any(old.get(k)!=v for k,v in expected.items()) or old.get('capacity_trial_author_attempted')
            or old.get('capacity_trial_phase_recovery_attempted')):
        raise Halt('Require the preserved partial authority and unattempted bounded trial boundary')
    fault=old.get('capacity_trial_load_outcome',{})
    if (fault.get('policy')!='simultaneous-capacity-trial-v1' or fault.get('candidate')!=SOURCE
            or fault.get('cause')!='compressor-growth-above2GiB' or fault.get('author_requests')!=0
            or not fault.get('all_owned_processes_stopped')):
        raise Halt('Require the diagnosed load-only compression stop before the changed phase-aware attempt')
    if old.get('player_death_focused_fault',{}).get('cause')!='resident available-memory guard':
        raise Halt('Require the measured resource diagnosis before capacity qualification')


class CapacityAuthor(FocusedDeath):
    phases=(('install-walk',('Bootstrap.cs',),
        'Perform one useful bounded part of the death integration: install the supplied current '
        'DeathAuthority once in Bootstrap using the actual player/camera, and make Walker obey its '
        'IsDead decision for horizontal player input. Preserve gravity/ground contact, living speed '
        'and turning, existing component order and all reset behavior. Preserve the entire Follow '
        'camera/reticle class byte-for-byte. The corrected authority clears only on the ordinary '
        'Restarts edge. Do not edit that authority, vehicle, combat, chapters or HUD in this small '
        'qualification task. Those remain pending; do not claim the whole death contract is repaired.'),)

    def __init__(self,*args,**kwargs):
        import psutil
        super().__init__(*args,**kwargs)
        receipt=read_json(self.store.root/'private/current-capacity-trial.json')
        if receipt.get('policy')!=POLICY:raise Halt('Explicit scoped trial receipt is required')
        supervisor=psutil.Process(receipt['supervisor_pid']);server=psutil.Process(receipt['server_pid'])
        if (abs(supervisor.create_time()-receipt['supervisor_start'])>.01
                or abs(server.create_time()-receipt['server_start'])>.01
                or server.ppid()!=supervisor.pid):
            raise Halt('Preserve changed resident process ownership')
        self.machine.capacity_budget=Budget(self.store.root/'private/capacity-controller-budget.jsonl')
        self.machine.capacity_budget.set_owned_pid(server.pid)

    def validate_recovery(self,old):
        validate_boundary(old)
        self.red=old['player_death_red_outcome']
        self.resume_capacity=self.priority_resume=self.transport_recovery=self.admission_recovery=False

    def recovery_settings(self):
        return dict(capacity_trial_author_attempted=True,capacity_trial_phase_recovery_attempted=True,
            recovery_route='phase-aware-useful-capacity-qualification',
            shared_workload_priority='simultaneous-no-default-priority',
            shared_priority_user_utc='2026-10-07T00:51:00Z',
            recovery_change='Same local model/xhigh quality; official safe dynamic accounting plus measured '
            'Unreal growth/OS/request reserves, phase-aware sustained compression checks, original '
            'swap/thermal/graphics/speed guards and rollback; preserve the original load-only fault.')

    def finish_author(self,ident,result):
        result.update(complete_death_integration=False,capacity_policy=POLICY,native_verified=False)
        atomic(self.store.root/'evidence'/(ident+'-capacity-author.json'),result)
        self.store.set(stage='capacity-trial-source-saved-awaiting-native',capacity_trial_source_outcome=dict(
            candidate=self.store.get('source_checkpoint'),round=ident,local_authored=True,
            changed_files=result['changed_files'],native_verified=False,complete_death_integration=False))
        self.store.report()
        raise Halt('Capacity trial saved local install/walk source; inspect capacity evidence and unload idle model before native verification')


if __name__=='__main__':raise SystemExit(main(CapacityAuthor))
