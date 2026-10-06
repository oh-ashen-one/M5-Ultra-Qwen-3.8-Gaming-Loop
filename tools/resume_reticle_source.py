#!/usr/bin/env python3
"""Local Qwen repairs only the inspected reticle render implementation."""
import json

from resume_character_camera import CharacterCamera, BOOT, ACCEPTED
from resume_camera_native_only import SOURCE
from resume_three_day_queue import main
from loop_controller.core import Files, Halt, atomic, read_json, sha
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.model import tool
from loop_controller.small_edits import SelectedEdit
from loop_controller.visual_context import TARGETS, contract

PRIOR = 'q0134-e549c186'
TASK = dict(id='reticle-render-repair', phase='polish', visual_facing=True,
    outcome='Local-authored reticle marking the actual camera-center aim in both render paths')
MARKER = '        // ---- restrained center-ray reticle'


class ReticleSource(CharacterCamera):
    reticle_output_tokens = 8192
    def validate_recovery(self, old):
        expected = dict(status='paused', controller_pid=None, owned_process=None,
            current_round=PRIOR, source_checkpoint=SOURCE, last_playable_checkpoint=ACCEPTED,
            task_index=7, task_failures=24, failure_streak=1, diagnosis_used=True,
            overall_deadline_epoch=HARD_CAP_EPOCH,
            blocker='Halt: Reticle dual-render before evidence complete; inspect both actual render paths before local repair')
        if any(old.get(k) != v for k, v in expected.items()) or old.get('reticle_render_repair_attempted'):
            raise Halt('Require the preserved dual-render source-matched diagnostic boundary')
        self.before = self.store.root / 'evidence' / PRIOR
        self.inspection = read_json(self.before / 'dual-render-pixel-inspection.json')
        receipt = read_json(self.before / 'dual-render-receipt.json')
        if (self.inspection.get('candidate') != SOURCE or not self.inspection.get('inspected_actual_pixels')
                or self.inspection.get('offscreen_reticle_visible') is not False
                or not receipt.get('native_passed')):
            raise Halt('Require actual red reticle pixels and a clean native diagnostic')
        for row in receipt['images']:
            if sha((self.before / 'captures' / row['file']).read_bytes()) != row['sha256']:
                raise Halt('The inspected source-matched image changed')
        self.resume_capacity = self.priority_resume = self.transport_recovery = self.admission_recovery = False

    def wait_for_capacity(self):
        self.capacity.wait('local-reticle-render-repair')

    def recovery_settings(self):
        return dict(reticle_render_repair_attempted=True, recovery_route='inspected-dual-render-local-repair',
            recovery_change='Use exact rendering span, actual normal/offscreen pixels and Unity API context; '
            'high reasoning with bounded output; save local source before a deliberate model-unloaded native phase.')

    def work(self):
        ident = self.begin(TASK, 'local-reticle-render-repair')
        files = Files(self.project, self.store)
        original = files.path(BOOT).read_text()
        start = original.index(MARKER)
        end = original.rindex('    }\n}')
        selected = SelectedEdit(files, BOOT, original[:start].count('\n') + 1,
            original[:end].count('\n'), max_lines=140)
        protected = {p: sha(p.read_bytes()) for p in self.project.rglob('*.cs') if p != files.path(BOOT)}

        def save(action, fields):
            content = fields['content']
            for forbidden in ('LoopInput', 'LoopSignals', 'LoopRuntime', 'GetCommandLineArgs', 'LateUpdate',
                              'FixedUpdate', 'Time.timeScale', 'System.IO', 'System.Reflection', 'class Follow'):
                if forbidden in content:
                    raise ValueError('Only rendering/lifetime implementation in the supplied reticle span: ' + forbidden)
            if content.strip() == selected.old.strip() or 'OnPostRender' not in content:
                raise ValueError('Save the actual bounded reticle rendering correction')
            result = selected.apply(action, content)
            self.store.set(source_checkpoint=self.checkpoint_source('Local Qwen: repair reticle in both camera render paths'))
            self.store.report()
            return result

        images = [('COMBAT TARGET; aspiration, not native output', self.refs / TARGETS[2]),
            ('BEFORE ACTUAL Camera.Render target PNG at 3.2 seconds', self.before / 'captures/frame-000.png'),
            ('BEFORE ACTUAL normal player-screen PNG at 3.2 seconds', self.before / 'captures/screen-000.png')]
        shader = files.path('Assets/Resources/HudOpaque.shader').read_text()
        self.c.update(working_context_tokens=65536, output_tokens=self.reticle_output_tokens, model_timeout_seconds=600)
        result = self.model.session('builder', ident + '-reticle-source',
            'You are local Qwen, sole game-code author. Repair the concrete reticle rendering defect using the exact APIs and actual images.',
            'The camera source passed its 95-second gameplay replay, all ten regressions, and the wall/near-plane '
            'clearance probe. Preserve that camera positioning and every gameplay mechanic. Only replace the supplied '
            'reticle method span, with any small rendering helper/lifetime method needed inside that span. '
            'The field Material reticleMat already exists on Follow, which is on the enabled MainCamera. '
            'Native pixels expose the defect; source also contradicts its own Camera.Render comment by returning '
            'when camera.targetTexture is non-null. Provide a restrained high-contrast reticle exactly centered on '
            'Combat\'s camera.transform.forward ray in BOTH a normal native player window and an explicit offscreen '
            'Camera.Render target. Handle each render surface\'s dimensions correctly. Use a shader actually included '
            'in this player; do not rely on a Shader.Find name that may have been stripped. Preserve the image and '
            'depth state needed by subsequent rendering. Avoid per-frame material allocation and destroy only your '
            'owned material at lifecycle end. No packages, new assets, new files, camera physics, aim assist, test '
            'detection, mission/health/input changes or source outside the selected span. Choose a sound minimal '
            'rendering solution; do not merely remove one guard without checking dimensions, shader color behavior '
            'and the actual render path. High thinking effort is enabled for this integration; return the complete '
            f'compact replacement through finish_source within {self.reticle_output_tokens} output tokens. No planning essay is needed.\n'
            'VERIFIED API CONTEXT: Unity 6000 Built-in pipeline calls MonoBehaviour.OnPostRender on a Camera component '
            'after its scene render, including Camera.Render. The external capture saves/restores camera.targetTexture '
            'and RenderTexture.active around Camera.Render to a 960x540 RenderTexture, then ReadPixels. A separate '
            'normal-window capture waits for WaitForEndOfFrame and uses Texture2D.ReadPixels on the screen framebuffer; '
            'its resolution may differ. API references: '
            'https://docs.unity3d.com/6000.0/Documentation/ScriptReference/MonoBehaviour.OnPostRender.html ; '
            'https://docs.unity3d.com/6000.0/Documentation/ScriptReference/GL.LoadPixelMatrix.html .\n'
            'The included Resources shader below is available as Resources.Load<Shader>("HudOpaque"). Its fragment '
            'uses uniform _Color, not incoming vertex colors; account for the actual shader semantics if using it. '
            'Other shader availability must not be assumed.\nINCLUDED SHADER:\n' + shader +
            '\nACTUAL PIXEL INSPECTION:\n' + json.dumps(self.inspection) +
            '\nEXACT REPLACEABLE RETICLE SPAN (no closing class or namespace braces):\n' + selected.old,
            [tool('finish_source', 'Save the complete reticle-only replacement span; native verification follows.',
                  {'content': {'type': 'string'}})], {'finish_source': save},
            images=images, visual_contract=contract(images, [TARGETS[2]], 2), turns=2, reasoning_effort='xhigh',
            retained_assistant=getattr(self, 'retained_assistant', None))
        atomic(self.store.root / 'evidence' / (ident + '-reticle-author.json'), result)
        if not result.get('ok') or files.path(BOOT).read_text() == original:
            raise Halt('No complete reticle source saved; preserve the bounded local response for diagnosis')
        if any(sha(p.read_bytes()) != digest for p, digest in protected.items()):
            raise Halt('Reticle author changed protected source')
        self.store.set(stage='reticle-source-saved-awaiting-native',
            reticle_source_outcome=dict(candidate=self.store.get('source_checkpoint'), round=ident,
                before_evidence=PRIOR, local_authored=True, native_verified=False, final_game_accepted=False))
        self.store.report()
        raise Halt('Local reticle source saved; unload the idle model deliberately before dual-render native verification')


if __name__ == '__main__':
    raise SystemExit(main(ReticleSource))
