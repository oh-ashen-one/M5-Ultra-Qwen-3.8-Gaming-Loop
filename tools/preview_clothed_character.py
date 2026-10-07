#!/usr/bin/env python3
"""Export the saved original character and inspect an early real Unity import."""
from author_clothed_character import ACCEPTED, ART, TASK, SAVED
from resume_camera_native_only import CameraNativeOnly
from resume_three_day_queue import main
from loop_controller.core import Halt, atomic, read_json, sha
from loop_controller.delivery_policy import HARD_CAP_EPOCH, queue_milestone


def validate_boundary(old):
    expected = dict(status='paused', controller_pid=None, owned_process=None,
        last_playable_checkpoint=ACCEPTED, task_index=7, task_failures=24,
        failure_streak=1, diagnosis_used=True, overall_deadline_epoch=HARD_CAP_EPOCH, blocker=SAVED)
    result = old.get('clothed_character_source_outcome', {})
    if (any(old.get(k) != v for k, v in expected.items()) or old.get('clothed_character_preview_attempted')
            or not result.get('local_authored') or result.get('candidate') != old.get('source_checkpoint')):
        raise Halt('Require the saved local character and unchanged stopped owner/history')


class PreviewClothedCharacter(CameraNativeOnly):
    def validate_recovery(self, old):
        validate_boundary(old)
        self.source = old['source_checkpoint']
        self.source_result = old['clothed_character_source_outcome']
        self.resume_capacity = self.priority_resume = self.transport_recovery = self.admission_recovery = False

    def recovery_settings(self):
        return dict(clothed_character_preview_attempted=True,
            recovery_route='early-clothed-character-export-native-preview',
            recovery_change='Inference unloaded; export local original source, checkpoint assets immediately and inspect real native idle/front/back images before runtime animation or acceptance.')

    def work(self):
        ident = self.begin(TASK, 'export-clothed-character')
        if sha((self.project/ART).read_bytes()) != self.source_result['script_sha256']:
            raise Halt('Saved local authoring source changed')
        exported = self.engines.blender(self.project, ART, ident+'-character-export')
        atomic(self.store.root/'evidence'/(ident+'-character-export.json'), exported)
        candidate = self.checkpoint_source('Local Qwen: export original clothed articulated character'
            if exported.get('ok') else 'Preserve failed original character export without success claim')
        self.store.set(source_checkpoint=candidate)
        self.store.report()
        if not exported.get('ok'):
            raise Halt('Local clothed character export failed; preserve source and actual Blender diagnostic')
        if (not exported.get('fresh_staged_export')
                or exported.get('script_sha256') != self.source_result['script_sha256']
                or any(sha((self.project/f['path']).read_bytes()) != f['sha256'] for f in exported['files'])):
            raise Halt('Successful native preview requires fresh source-matched export bytes')
        scenario = dict(id='clothed-character-early-native-preview', coverage='foundation', duration=18,
            steps=[dict(start=3,end=4,keys=['W']),dict(start=6,end=6.4,keys=['D']),
                   dict(start=9,end=9.5,keys=['S']),dict(start=12,end=12.1,keys=['R'])],
            captures=[1,3.5,6.3,10,12.5,17])
        bundle = self.store.root/'evidence'/(ident+'-character-preview')
        self.store.set(stage='native-clothed-character-early-preview'); self.store.report()
        gate = self.engines.unity(self.project, bundle, scenario, candidate)
        outcome = dict(candidate=candidate, prior_playable=ACCEPTED, export=exported,
            native_gate=gate, evidence=bundle.name, local_authored=True,
            visual_review='pending actual pixel inspection', runtime_animation='not yet integrated',
            gameplay_promotion=False, final_game_accepted=False)
        atomic(bundle/'character-preview.json', outcome)
        self.store.set(clothed_character_preview_outcome=outcome); self.store.report()
        frames = sorted((bundle/'captures').glob('frame-*.png'))
        if frames:
            queue_milestone(self.store, 'native-milestone', TASK, bundle, gate, frames,
                {f'frame-{i:03d}.png': t for i, t in enumerate(scenario['captures'])})
        if not gate.get('passed'):
            raise Halt('Local clothed character failed early native import/preview; preserve actual evidence')
        raise Halt('Clothed character exported and early native preview saved; inspect actual pixels then author runtime animation')


if __name__ == '__main__':
    raise SystemExit(main(PreviewClothedCharacter))
