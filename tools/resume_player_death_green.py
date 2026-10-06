#!/usr/bin/env python3
"""Verify the complete local death repair with identical negatives and healthy gameplay."""
import json
from resume_camera_native_only import CameraNativeOnly, ACCEPTED
from resume_three_day_queue import main
from qualify_moving_encounter import checked
from loop_controller.core import Halt, atomic, read_json
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.player_death_checks import CASES, death_probe, inspect_player_death
from loop_controller.continuous_tasks import TASKS

TASK = dict(id='chapter-player-death-green', phase='mission', visual_facing=False,
    outcome='All chapter death/reset boundaries and living-player gameplay regressions')


class PlayerDeathGreen(CameraNativeOnly):
    def validate_recovery(self, old):
        expected = dict(status='paused', controller_pid=None, owned_process=None,
            last_playable_checkpoint=ACCEPTED, task_index=7, task_failures=24,
            failure_streak=1, diagnosis_used=True, overall_deadline_epoch=HARD_CAP_EPOCH,
            player_death_source_attempted=True,
            blocker='Halt: Local death integration saved; unload the idle model for native green and healthy-route regressions')
        authored = old.get('player_death_source_outcome', {})
        if (any(old.get(k) != v for k, v in expected.items()) or old.get('player_death_green_attempted')
                or not authored.get('local_authored') or not authored.get('changed_files')
                or authored.get('candidate') != old.get('source_checkpoint')
                or authored.get('round') != old.get('current_round')):
            raise Halt('Require the complete local death integration checkpoint and unchanged accepted history')
        result = read_json(self.store.root / 'evidence' / (authored['round'] + '-death-author.json'))
        if not result.get('ok') or old.get('active_model_settings', {}).get('reasoning_effort') != 'xhigh':
            raise Halt('Require actual high-reasoning complete source submission before native green tests')
        self.source = old['source_checkpoint']
        self.resume_capacity = self.priority_resume = self.transport_recovery = self.admission_recovery = False

    def recovery_settings(self):
        return dict(player_death_green_attempted=True, recovery_route='local-death-green-and-healthy-regressions',
            recovery_change='Use the unchanged six declared zero-health cases, then the real95-second positive '
            'mission and all ten prior gameplay regressions on the current local source. Inference stays unloaded.')

    def work(self):
        ident = self.begin(TASK, 'native-chapter-player-death-green')
        original = read_json(self.store.root / 'evidence/q0132-45fc0624-positive/captures/scenario.json')
        outcome = dict(candidate=self.source, cases=[], positive='pending', regressions='pending', final_game_accepted=False)
        path = self.store.root / 'evidence' / (ident + '-player-death-green.json')
        def save():
            atomic(path, outcome); self.store.set(player_death_green_outcome=outcome); self.store.report()
        for case in CASES:
            bundle = self.store.root / 'evidence' / (ident + '-' + case)
            native = self.engines.unity(self.project, bundle, death_probe(original, case), self.source)
            if not native.get('passed'):
                outcome['failed_native_case'] = case; outcome['native_failure'] = native; save()
                raise Halt('Death repair failed native compile/runtime prerequisite: ' + case)
            captures = bundle / 'captures'
            rows = [json.loads(line) for line in (captures / 'trace.jsonl').read_text().splitlines()]
            result = inspect_player_death(rows, read_json(captures / 'death-injection.json'), case)
            result.update(candidate=self.source, build_id=native['build_id'], evidence=bundle.name)
            atomic(bundle / 'player-death-gate.json', result)
            outcome['cases'].append(result); save()
            if not result['passed']:
                raise Halt('Local death integration needs measured follow-up: ' + case + ': ' + json.dumps(result['failure']))
        self.store.set(stage='native-death-repair-healthy-route'); self.store.report()
        positive = self.store.root / 'evidence' / (ident + '-positive')
        raw = self.engines.unity(self.project, positive, original, self.source)
        outcome['positive'] = checked(positive, raw, 'positive') if raw.get('passed') else raw; save()
        if not outcome['positive'].get('passed'):
            raise Halt('Death repair regressed the ordinary living-player mission')
        self.store.set(stage='native-death-repair-all-regressions'); self.store.report()
        outcome['regressions'] = self.regress(TASKS[7], ident, self.source); save()
        if not outcome['regressions'].get('passed'):
            raise Halt('Death repair has a native gameplay regression; preserve all source and evidence')
        raise Halt('Local death repair passes six zero-health boundaries and healthy gameplay; inspect native failure/reset images')


if __name__ == '__main__':
    raise SystemExit(main(PlayerDeathGreen))
