#!/usr/bin/env python3
"""Check partial-source compilation/nonregression while shared inference is held."""
import json
from resume_camera_native_only import CameraNativeOnly, ACCEPTED
from resume_three_day_queue import main
from qualify_moving_encounter import checked
from loop_controller.core import Halt, atomic, read_json
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.player_death_checks import death_probe, inspect_player_death

SOURCE = 'ac0d7fe441a48377eb8d3bb420da2618ed797ed6'
TASK = dict(id='partial-death-source-native',phase='mission',visual_facing=False,
    outcome='Compile and healthy-route evidence for partial source; preserve expected red integration result')


class PartialDeathNative(CameraNativeOnly):
    def validate_recovery(self, old):
        expected=dict(status='paused',controller_pid=None,owned_process=None,current_round='q0144-dd98c86e',
            source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,task_index=7,task_failures=24,
            failure_streak=1,diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,
            player_death_focused_attempted=True,blocker='URLError: <urlopen error [Errno 61] Connection refused>')
        fault=read_json(self.store.root/'evidence/q0144-dd98c86e-resource-diagnosis.json')
        if (any(old.get(k)!=v for k,v in expected.items()) or old.get('partial_death_native_attempted')
                or fault.get('candidate')!=SOURCE or fault.get('cause')!='resident available-memory guard'
                or old.get('player_death_source_outcome')):
            raise Halt('Require the preserved incomplete local authority and diagnosed shared-memory stop')
        self.resume_capacity=self.priority_resume=self.transport_recovery=self.admission_recovery=False

    def recovery_settings(self):
        return dict(partial_death_native_attempted=True,recovery_route='partial-source-native-with-inference-unloaded',
            recovery_change='Compile and replay saved local source without inference; verify healthy route and '
            'preserve the expected remaining dead-control defect. No completed integration or promotion claim.')

    def work(self):
        ident=self.begin(TASK,'native-partial-death-source')
        original=read_json(self.store.root/'evidence/q0132-45fc0624-positive/captures/scenario.json')
        outcome=dict(candidate=SOURCE,complete_integration=False,model_unloaded=True,final_game_accepted=False)
        def save():
            atomic(self.store.root/'evidence'/(ident+'-partial-death-native.json'),outcome)
            self.store.set(player_death_partial_native_outcome=outcome);self.store.report()
        positive=self.store.root/'evidence'/(ident+'-positive')
        gate=self.engines.unity(self.project,positive,original,SOURCE)
        outcome['positive']=checked(positive,gate,'positive') if gate.get('passed') else gate;save()
        if not outcome['positive'].get('passed'):
            raise Halt('Partial death source failed native build/healthy route; preserve source and evidence')
        case='courier-pickup';bundle=self.store.root/'evidence'/(ident+'-'+case)
        gate=self.engines.unity(self.project,bundle,death_probe(original,case),SOURCE)
        if not gate.get('passed'):
            outcome['negative_native_failure']=gate;save()
            raise Halt('Partial-source red prerequisite failed; diagnose acceptance setup before game edits')
        cap=bundle/'captures';rows=[json.loads(x) for x in (cap/'trace.jsonl').read_text().splitlines()]
        red=inspect_player_death(rows,read_json(cap/'death-injection.json'),case)
        red.update(candidate=SOURCE,build_id=gate['build_id'],evidence=bundle.name)
        atomic(bundle/'player-death-gate.json',red);outcome['remaining_integration_red']=red;save()
        if not red.get('setup_passed'):
            raise Halt('Partial-source death setup failed; preserve genuine diagnostic failure')
        if red.get('passed'):
            raise Halt('Partial-source death unexpectedly passes; inspect the current trace before claiming integration')
        raise Halt('Partial death source compiles and preserves healthy route; dead controls remain unfixed and shared inference capacity is required')


if __name__=='__main__':raise SystemExit(main(PartialDeathNative))
