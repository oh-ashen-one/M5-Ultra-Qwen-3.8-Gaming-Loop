#!/usr/bin/env python3
"""Locally include the missing HUD shader instead of masking native startup failure."""
from resume_hud_presentation_polish import HudPresentationPolish, compact, PATH, STATUS
from resume_hud_live_objective import ACCEPTED
from resume_three_day_queue import main
from loop_controller.core import Files, Halt
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.model import tool

SOURCE = '099bd65455ae41ccc232de30ef7d2c4ddd8cd8c6'
ROUND = 'q0119-0570608e'
SHADER = 'Assets/Resources/HudOpaque.shader'


def validate_pause(old):
    expected = dict(source_checkpoint=SOURCE, last_playable_checkpoint=ACCEPTED, current_round=ROUND,
        task_index=7, task_failures=24, failure_streak=1, diagnosis_used=True,
        overall_deadline_epoch=HARD_CAP_EPOCH, stage='native-consolidated-hud-positive',
        hud_patch_transport_recovered=True,
        blocker='Halt: Owned engine deadline exceeded: unity-play')
    if any(old.get(k) != v for k, v in expected.items()) or old.get('hud_explicit_shader_attempted'):
        raise Halt('Require exact first missing-shader native failure and original history')


def validate_shader(content):
    if not isinstance(content, str) or len(content) > 4000 or len(content.splitlines()) > 70:
        raise ValueError('One small original unlit color shader, at most 70 lines')
    for required in ['Shader "Chicago/HudOpaque"', '_Color', 'Properties', 'SubShader', 'Pass',
                     'CGPROGRAM', '#pragma vertex', '#pragma fragment', 'UnityObjectToClipPos', 'ENDCG']:
        if required not in content: raise ValueError('Missing shader interface: ' + required)
    for forbidden in ['GrabPass', 'UsePass', 'Fallback', 'Compute', 'tex2D', 'sampler2D', 'sin(', 'cos(', '_Time', 'clip(', 'discard']:
        if forbidden in content: raise ValueError('Only constant unlit color output is in scope')
    if '"Queue"="Overlay"' in compact(content):
        raise ValueError('Opaque geometry queue must keep TextMesh text rendered above the backing')
    return content


class HudShaderRecovery(HudPresentationPolish):
    def validate_recovery(self, old):
        validate_pause(old)
        self.resume_capacity = False; self.priority_resume = False; self.transport_recovery = False
        p = self.store.root / 'evidence' / (ROUND + '-positive') / 'captures/runtime-errors.txt'
        first = p.read_text()[:2500]
        if not first.startswith('ArgumentNullException: Value cannot be null.\nParameter name: shader') or 'MissionDirectorHud.Setup' not in first:
            raise Halt('Preserve a different native initialization failure')
        if (self.project / SHADER).exists(): raise Halt('Do not overwrite an existing shader')
        for path in (PATH, STATUS):
            if (self.project / path).read_text().count('Shader.Find("Unlit/Color")') != 1:
                raise Halt('Expected exactly one diagnosed missing shader lookup per HUD owner')

    def recovery_settings(self):
        return dict(hud_explicit_shader_attempted=True, recovery_route='local-explicit-HUD-shader-inclusion',
            recovery_change='The native runtime returned null for Unlit/Color. Local Qwen authors an original '
            'Resources shader and replaces only the two lookups with Resources.Load. Preserve failed source/logs; '
            'native initialization errors now stop the owned player promptly instead of waiting for its deadline.')

    def source(self, ident):
        self.c.update(output_tokens=2048, model_timeout_seconds=120)
        self.store.set(stage='local-original-HUD-shader'); self.store.report()
        files = Files(self.project, self.store)
        self.model.session('builder', ident + '-opaque-shader',
            'You are local Qwen authoring one original minimal Unity built-in-pipeline shader.',
            'Native startup proves Shader.Find("Unlit/Color") returns null in this standalone build. '
            'Author ONLY Assets/Resources/HudOpaque.shader, named Shader "Chicago/HudOpaque". '
            'One Properties color _Color, default(.06,.07,.085,1), one SubShader/Pass. Built-in Unity CG/HLSL: '
            'include UnityCG.cginc, simple POSITION vertex input transformed with UnityObjectToClipPos, '
            'fragment returns only _Color. Opaque Geometry queue (or its defaults), ordinary depth test/write and '
            'Cull Back; no lighting, textures, time, blending, overlay queue, fallback, borrowed code or dependencies. '
            'TextMesh renders in its later queue; do not draw this backing over text. This original Resources '
            'asset is included explicitly and loaded by its resource name. Submit complete shader via finish_source.',
            [tool('finish_source', 'Save the one original HUD shader.', {'content': {'type': 'string'}})],
            {'finish_source': lambda action, f: files.create(action, SHADER, validate_shader(f['content']))},
            turns=2, reasoning_effort='low')
        if not (self.project / SHADER).exists(): raise Halt('Local original HUD shader was not saved')
        candidate = self.checkpoint_source('Local Qwen: original explicitly included HUD shader')
        self.store.set(source_checkpoint=candidate, candidate_commit=candidate)
        for label, path in [('board-shader-resource', PATH), ('status-shader-resource', STATUS)]:
            line = next(line for line in (self.project / path).read_text().splitlines(True) if 'Shader.Find("Unlit/Color")' in line)
            expected = line.replace('Shader.Find("Unlit/Color")', 'Resources.Load<Shader>("HudOpaque")')
            self.patch(ident, label, path, line,
                'Replace only Shader.Find("Unlit/Color") with Resources.Load<Shader>("HudOpaque"). '
                'Preserve this line\'s variable, material construction and other text. Your original shader now '
                'lives at Assets/Resources/HudOpaque.shader; never mask load errors with an unrelated fallback.',
                lambda value, _, expected=expected: compact(value) == compact(expected), 2)
        return self.store.get('source_checkpoint')


if __name__ == '__main__': raise SystemExit(main(HudShaderRecovery))
