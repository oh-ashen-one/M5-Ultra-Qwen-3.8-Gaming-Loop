#!/usr/bin/env python3
"""Requalify the preserved street after fixing an incomplete native scene recorder."""
import json
from resume_saved_door import SavedDoor, SECOND_TASK, ACCEPTED
from resume_three_day_queue import main
from qualify_map_extension import promote_qualified_extension
from loop_controller.core import Halt, sha
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.runner import git

SOURCE='1ebf314a8cbcb96e5615b065c82339ff2afbc447'
CANDIDATE='6f9244b9045039e0749cd85489e55114b345e448'
ROUND='q0082-a3bd4b73'
EVIDENCE='q0081-785afd9c'
HASHES={'scoped-gate.json':'f0ac5c90f054300a85cbeba14e3759f141bea5d01fc31e3eb7b37c88cfb711ab',
    'captures/scenario.json':'e3affe7d53ae4f4de5aefeb24f849826ac98430dce21ebe56e6442eda0c92081',
    'captures/scene-transforms.json':'fb356fd1f934fb5f773088aa897b34cf8e3a387e0e550a616b35979d67231237',
    'captures/trace.jsonl':'6e4b648e365105e5cd7f4f2a4244082632241013f6f7369ddd32bb0dcfb50678'}


def validate_pause(old):
    expected=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=ROUND,
        task_index=7,task_failures=21,failure_streak=1,diagnosis_used=True,
        overall_deadline_epoch=HARD_CAP_EPOCH,blocker='Halt: Explicit controller stop',
        street_native_probe_attempted=True,saved_door_accepted=False,second_street_attempts=2)
    if any(old.get(k)!=v for k,v in expected.items()) or old.get('complete_inventory_recovery_attempted'):
        raise Halt('Expected exact recorder-diagnosis pause and preserved local source')


class CompleteInventory(SavedDoor):
    preserved_source=SOURCE
    native_attempt=1

    def validate_recovery(self,old):
        validate_pause(old)
        self.validate_recorded_fault()

    def validate_recorded_fault(self):
        bundle=self.store.root/'evidence'/EVIDENCE
        for name,expected in HASHES.items():
            if sha((bundle/name).read_bytes())!=expected:raise Halt('Original incomplete evidence changed: '+name)
        gate=json.loads((bundle/'scoped-gate.json').read_text())
        objects=json.loads((bundle/'captures/scene-transforms.json').read_text())['objects']
        if (gate.get('candidate_commit')!=CANDIDATE or gate.get('failure')!=['WorldCollision/AlleyDumpster:missing-original-components']
                or sum(o.get('kind')=='renderer' for o in objects)!=2048):
            raise Halt('Expected measured scene-recording cap, not another gameplay fault')
        if git(self.repo,'diff','--name-only',CANDIDATE,self.preserved_source,'--','game')!='game/Assets/Game/WorldColliders.cs':
            raise Halt('Preserve unexpected intervening game changes')
        self.accepted_probe()

    def recovery_settings(self):
        return dict(complete_inventory_recovery_attempted=True,
            recovery_route='full-scene-inventory-qualification',
            recovery_change='Preserve speculative local collider edit in Git; re-run prior street source and unchanged physical probe with complete native records')

    def work(self):
        # Preserve the intervening local edit in ancestry. Restore only this
        # task's game tree to the explicitly requested prior candidate.
        git(self.repo,'restore','--source='+CANDIDATE,'--','game')
        git(self.repo,'add','--','game')
        git(self.repo,'-c','user.name=Evidence controller',
            '-c','user.email=254017794+oh-ashen-one@users.noreply.github.com',
            'commit','-m','Requalify preserved local street after scene-recorder truncation')
        restored=git(self.repo,'rev-parse','HEAD')
        if git(self.repo,'diff','--name-only',CANDIDATE,'HEAD','--','game'):
            raise Halt('Restored game differs from the pinned local street')
        self.store.set(source_checkpoint=restored,candidate_commit=CANDIDATE,
            preserved_speculative_source=self.preserved_source,complete_inventory_native_attempts=self.native_attempt)
        self.store.event('restore-street-for-complete-observation',source=CANDIDATE,
            restored_checkpoint=restored,preserved_local_edit=self.preserved_source,
            source_bytes_equal=True,cloud_game_code_authored=False,
            support_and_prop_requirements_unchanged=True)
        ident=self.begin(SECOND_TASK,'complete-inventory-native-qualification')
        probe=json.loads((self.store.root/'evidence'/EVIDENCE/'captures/scenario.json').read_text())
        bundle,gate,failure=self.qualify(SECOND_TASK,ident,CANDIDATE,probe)
        if failure:
            self.record_rejection(SECOND_TASK,ident,CANDIDATE,failure)
            # The previous two source/native attempts remain recorded. Any real
            # gap now goes to the local author with complete native evidence.
            return self.after_native_failure()
        record=promote_qualified_extension(self,SECOND_TASK,bundle,gate,json.loads((bundle/'critic.json').read_text()))
        return self.continue_after_street(record)

    def after_native_failure(self):
        return self.advance_second_street(start_attempt=3)


if __name__=='__main__':raise SystemExit(main(CompleteInventory))
