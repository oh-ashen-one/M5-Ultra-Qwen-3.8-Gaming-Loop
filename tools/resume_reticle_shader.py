#!/usr/bin/env python3
"""Repair the saved local reticle's verified Unity API incompatibility."""
import json
from resume_reticle_source import ReticleSource, BOOT, MARKER
from resume_camera_native_only import ACCEPTED
from resume_three_day_queue import main
from loop_controller.core import Files, Halt, atomic, read_json, sha
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.model import tool
from loop_controller.small_edits import SelectedEdit
from loop_controller.visual_context import TARGETS, contract

PRIOR = 'q0136-d3f42928'
SOURCE = 'ae4e58e957fa237daedfcabed454e307b0b7b4ab'
SHADER = 'Assets/Resources/ReticleOverlay.shader'
TASK = dict(id='reticle-supported-render-state', phase='polish', visual_facing=True,
    outcome='Compileable original reticle shader and matching local-authored rendering span')


class ReticleShader(ReticleSource):
    def validate_recovery(self, old):
        expected = dict(status='paused', controller_pid=None, owned_process=None,
            current_round=PRIOR, source_checkpoint=SOURCE, last_playable_checkpoint=ACCEPTED,
            task_index=7, task_failures=24, failure_streak=1, diagnosis_used=True,
            overall_deadline_epoch=HARD_CAP_EPOCH,
            blocker='Halt: Local reticle source saved; unload the idle model deliberately before dual-render native verification')
        if any(old.get(k) != v for k, v in expected.items()) or old.get('reticle_shader_attempted'):
            raise Halt('Require the saved local rendering source and preserve the exact prior failures')
        self.api_review = read_json(self.store.root / 'evidence' / (PRIOR + '-reticle-api-review.json'))
        if self.api_review.get('candidate') != SOURCE or self.api_review.get('native_compilation_attempted'):
            raise Halt('Require the exact installed-API static review; do not invent a native compiler result')
        self.before = self.store.root / 'evidence/q0134-e549c186'
        self.resume_capacity = self.priority_resume = self.transport_recovery = self.admission_recovery = False

    def recovery_settings(self):
        return dict(reticle_shader_attempted=True, recovery_route='local-reticle-supported-shader-state',
            recovery_change='Preserve the saved incompatible GL source. Supply installed Unity API evidence and '
            'allow one original shader plus its matching rendering span, high reasoning and16384output tokens.')

    def work(self):
        ident = self.begin(TASK, 'local-reticle-supported-shader')
        files = Files(self.project, self.store)
        original = files.path(BOOT).read_text()
        start = original.index(MARKER); end = original.rindex('    }\n}')
        selected = SelectedEdit(files, BOOT, original[:start].count('\n') + 1,
            original[:end].count('\n'), max_lines=140)
        protected = {p: sha(p.read_bytes()) for p in self.project.rglob('*')
            if p.is_file() and p.suffix in ('.cs', '.shader') and p != files.path(BOOT)}
        if files.path(SHADER).exists():
            raise Halt('Do not overwrite an unrelated shader')

        def save(action, fields):
            span, shader = fields['reticle_span'], fields['shader_source']
            if not isinstance(span, str) or len(span.encode()) > 6000 or len(span.splitlines()) > 140:
                raise ValueError('Keep the complete replacement rendering span within6KB/140lines')
            if not isinstance(shader, str) or len(shader.encode()) > 6000 or len(shader.splitlines()) > 140:
                raise ValueError('One compact original Unity shader within6KB/140lines')
            for invalid in ('GL.Disable', 'GL.Enable', 'GL.DepthMask', 'GL_DEPTH_TEST', 'LoopInput',
                            'LoopRuntime', 'LoopSignals', 'LateUpdate', 'FixedUpdate', 'System.IO', 'GL.Clear'):
                if invalid in span:
                    raise ValueError('Rendering scope or installed API violation: ' + invalid)
            if 'OnPostRender' not in span or 'ReticleOverlay' not in span:
                raise ValueError('Use the included original reticle shader in both camera paths')
            files.create(action + '-shader', SHADER, shader)
            result = selected.apply(action + '-reticle', span)
            self.store.set(source_checkpoint=self.checkpoint_source('Local Qwen: supported reticle overlay shader and render state'))
            self.store.report()
            return result

        images = [('COMBAT TARGET; aspiration only', self.refs / TARGETS[2]),
            ('ACTUAL BEFORE offscreen camera render at3.2s', self.before / 'captures/frame-000.png'),
            ('ACTUAL BEFORE normal player screen at3.2s', self.before / 'captures/screen-000.png')]
        self.c.update(working_context_tokens=65536, output_tokens=16384, model_timeout_seconds=600)
        result = self.model.session('builder', ident + '-reticle-source',
            'You are local Qwen, sole substantive game author. Repair the saved rendering implementation using supported Unity APIs.',
            'Your prior complete source is preserved, but static review of the actual installed UnityEngine.CoreModule '
            'API found nonexistent GL.Disable, GL.Enable, GL.DepthMask and GL_DEPTH_TEST. No native compile was '
            'attempted for that source, and it is not accepted. Keep your useful centering, material ownership and '
            'dual-target design. The previous existing-shader-only restriction was too narrow: you may now author ONE '
            'original Resources/ReticleOverlay.shader and the matching reticle-only C# span. Use supported ShaderLab '
            'render states in that shader for a visible overlay with no scene depth writes or buffer clearing. '
            'Its color semantics and winding must agree with the C# drawing. No OpenGL state calls, native plugins '
            'or new packages. Retain the camera-motion/physics prefix verbatim; all gameplay and other shaders are '
            'protected. No per-frame material creation, hide actors, input/health changes or acceptance detection. '
            'Load the shader through Resources and preserve/destroy only owned material. The reticle must appear '
            'at the actual center ray in both the normal game screen and Camera.Render targets at differing resolutions. '
            'Both original before images have no visible reticle. Shader stripping is a possible additional cause, '
            'not a proven diagnosis: avoid definitive unsupported claims in comments.\n'
            'Use high reasoning for API correctness, then call finish_source with the complete reticle_span and '
            'shader_source.16,384output tokens are available, but this focused integration should stay concise. '
            'Do not repeat previous design analysis. The controller will compile and inspect actual pixels.\n'
            'OFFICIAL REFERENCES: https://docs.unity3d.com/6000.0/Documentation/ScriptReference/GL.html ; '
            'https://docs.unity3d.com/6000.0/Documentation/Manual/SL-ZTest.html ; '
            'https://docs.unity3d.com/6000.0/Documentation/Manual/SL-ZWrite.html . '
            'ShaderLab Pass render-state commands control depth test, depth writes and culling; these are not GL methods.\n'
            'INSTALLED API EVIDENCE:\n' + json.dumps(self.api_review) +
            '\nEXACT CURRENT RETICLE SPAN; Material reticleMat already exists before this span:\n' + selected.old +
            '\nSHIPPED HUD SHADER AS API/PIPELINE CONTEXT ONLY; DO NOT MODIFY:\n' + files.path('Assets/Resources/HudOpaque.shader').read_text(),
            [tool('finish_source', 'Save the complete matching original shader and reticle C# implementation.',
                  {'reticle_span': {'type': 'string'}, 'shader_source': {'type': 'string'}})], {'finish_source': save},
            images=images, visual_contract=contract(images, [TARGETS[2]], 2), turns=2, reasoning_effort='xhigh')
        atomic(self.store.root / 'evidence' / (ident + '-reticle-author.json'), result)
        if not result.get('ok') or not files.path(SHADER).exists() or files.path(BOOT).read_text() == original:
            raise Halt('Local reticle shader source incomplete; preserve the bounded response and files')
        if any(sha(p.read_bytes()) != digest for p, digest in protected.items()):
            raise Halt('Reticle author changed protected source')
        self.store.set(stage='reticle-source-saved-awaiting-native',
            reticle_source_outcome=dict(candidate=self.store.get('source_checkpoint'), round=ident,
                before_evidence='q0134-e549c186', local_authored=True, native_verified=False, final_game_accepted=False))
        self.store.report()
        raise Halt('Local reticle source saved; unload the idle model deliberately before dual-render native verification')


if __name__ == '__main__':
    raise SystemExit(main(ReticleShader))
