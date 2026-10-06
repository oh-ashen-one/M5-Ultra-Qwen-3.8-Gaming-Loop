#!/usr/bin/env python3
"""Repair the saved local character's observed Blender API/transform defects."""
from resume_character_artifact import CharacterArtifact, ART, ACCEPTED, TASK, validate_character
from resume_three_day_queue import main
from loop_controller.core import Files, Halt, atomic, read_json, sha
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.model import tool
from loop_controller.visual_context import TARGETS, contract

PRIOR = 'q0129-ac8d31db'
SOURCE = 'ab5992e4cc0291a30cfc8d270f116bc2c275afae'
SCRIPT = '9262f8ca47cc2d57ce1082231056e76c77d9536706d791ac36e787bc868a421b'


class CharacterExport(CharacterArtifact):
    def validate_recovery(self, old):
        expected = dict(status='paused', controller_pid=None, owned_process=None,
            current_round=PRIOR, source_checkpoint=SOURCE, last_playable_checkpoint=ACCEPTED,
            task_index=7, task_failures=24, failure_streak=1, diagnosis_used=True,
            overall_deadline_epoch=HARD_CAP_EPOCH, stage='export-original-character',
            runtime_character_recovery_attempted=True,
            blocker='Halt: Original character saved but Blender export failed; preserve source and diagnostics')
        if any(old.get(k) != v for k, v in expected.items()) or old.get('character_export_repair_attempted'):
            raise Halt('Require the preserved first character export failure')
        self.failure = read_json(self.store.root / 'evidence' / (PRIOR + '-character-export.json'))
        if self.failure.get('ok') or "type object 'Matrix' has no attribute 'Euler'" not in self.failure.get('diagnostic', ''):
            raise Halt('Require the actual Blender API failure, not an unrelated engine/resource error')
        if sha((self.project / ART).read_bytes()) != SCRIPT:
            raise Halt('Preserve the complete local-authored character source')
        self.before = self.store.root / 'evidence/q0126-657b9ebf-positive'
        self.resume_capacity = self.priority_resume = self.transport_recovery = self.admission_recovery = False

    def recovery_settings(self):
        return dict(character_export_repair_attempted=True, recovery_route='local-character-export-api-repair',
            recovery_change='Keep the complete saved character. Local Qwen repairs its actual Blender API '
            'failure and consistent world/local transforms, then re-export and inspect actual Unity pixels.')

    def work(self):
        ident = self.begin(TASK, 'local-character-export-repair')
        files = Files(self.project, self.store)
        original = files.path(ART).read_text()
        protected = {p: sha(p.read_bytes()) for p in self.project.rglob('*.cs')}
        def save(action, fields):
            content = validate_character(fields['content'])
            if sha(content.encode()) == SCRIPT:
                raise ValueError('Save the corrected complete source')
            result = files.edit(action, ART, SCRIPT, content=content)
            self.store.set(source_checkpoint=self.checkpoint_source('Local Qwen: repair character export'),
                           stage='original-character-source-saved')
            self.store.report()
            return result
        images = [('CHARACTER ART-DIRECTION TARGET; aspiration', self.refs / TARGETS[0]),
                  ('OLD NATIVE BASELINE; new saved character has not exported yet', self.before / 'captures/frame-000.png')]
        self.c.update(working_context_tokens=65536, output_tokens=8192, model_timeout_seconds=600)
        result = self.model.session('builder', ident + '-repair-character-export',
            'You are local Qwen. Repair your saved Blender character and submit the complete file now.',
            'The complete character file was saved successfully. Blender5.2 failed in rot(): '
            "AttributeError: type object 'Matrix' has no attribute 'Euler'. "
            'Correct the supported mathutils Euler-to-4x4 rotation API. Also inspect the exact source for '
            'world/local transform consistency: mk assigns matrix_world, but torso callers supply absolute '
            'coordinates while head, arm, leg and gun mesh callers supply parent-local coordinates. '
            'Preserve the authored geometry, colors and named pivots; make these coordinates explicit and '
            'consistent so the body is assembled once. Preserve the0.79m presentation lift and1.80m anatomy. '
            'Do not redesign the character or edit C#. Keep the actual Blender API and parent transforms '
            'correct; update dependencies before reading parent world matrices if required. '
            'Use low thinking to save one complete compact Art/player.py through finish_source now. '
            'No external assets, downloads, file I/O or networking. The fixed adapter exports and captures '
            'Unity automatically. The attached native picture is the old baseline, not the failed new export.\n'
            'CURRENT COMPLETE SOURCE:\n' + original,
            [tool('finish_source', 'Save the complete corrected character source.', {'content': {'type': 'string'}})],
            {'finish_source': save}, images=images, visual_contract=contract(images, [TARGETS[0]], 1),
            turns=2, reasoning_effort='low')
        atomic(self.store.root / 'evidence' / (ident + '-character-author.json'), result)
        if not result.get('ok') or any(sha(p.read_bytes()) != digest for p, digest in protected.items()):
            raise Halt('Character export repair did not save a valid scoped artifact')
        self.export_and_preview(ident)


if __name__ == '__main__':
    raise SystemExit(main(CharacterExport))
