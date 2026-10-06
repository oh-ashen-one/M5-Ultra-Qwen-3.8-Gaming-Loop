#!/usr/bin/env python3
"""Local fixes for measured HUD lighting, tiny status text and missing reset hint."""
import json
import math
import re
from resume_hud_live_objective import HudLiveObjective, CAPACITY_SOURCE as SOURCE, ACCEPTED
from resume_hud_bounded_review import review_hud
from resume_consolidated_hud import TASK, PATH
from resume_three_day_queue import main
from loop_controller.core import Files, Halt, atomic, read_json, sha
from loop_controller.small_edits import SelectedEdit
from loop_controller.model import tool
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.continuous_tasks import TASKS

ROUND = 'q0117-d2caf437'
OUTCOME_SHA = '7e6b54aff4a9045db6b9fd9af033c1aed882d5e58687d3ddd5b006502813e99c'
STATUS = 'Assets/Game/HudStatus.cs'


def validate_pause(old):
    transport = old.get('current_round') == 'q0118-ca136f22' and old.get('hud_presentation_polish_attempted')
    expected = dict(source_checkpoint=SOURCE, last_playable_checkpoint=ACCEPTED, current_round=ROUND,
        task_index=7, task_failures=24, failure_streak=1, diagnosis_used=True,
        overall_deadline_epoch=HARD_CAP_EPOCH,
        blocker='Halt: Focused HUD review recorded; continue measured local gameplay and visual work')
    if transport:
        expected.update(current_round='q0118-ca136f22',
            blocker='Halt: Local bounded correction was not saved: objective-unlit-backing')
    if (any(old.get(k) != v for k, v in expected.items())
        or (old.get('hud_presentation_polish_attempted') and not transport)
        or old.get('hud_patch_transport_recovered')):
        raise Halt('Require exact completed HUD critic boundary and unchanged history')
    review = old.get('consolidated_hud_outcome', {}).get('review', {})
    if not review.get('ok') or review.get('verdict') != 'FIX':
        raise Halt('Require actual local HUD FIX verdict')


def compact(value):
    value = re.sub(r'(?<![\w.])0\.(\d+)f', r'.\1f', value)
    return re.sub(r'\s+', '', value)


def exact_content(value, accept, old):
    if accept(value, old): return value
    # Some tool transports escape the complete content string one extra time.
    # Decode only a whole JSON string and only if the same bounded validator accepts.
    if '\n' not in value and '\\n' in value and '\\"' in value:
        try: decoded = json.loads('"' + value + '"')
        except json.JSONDecodeError: decoded = None
        if isinstance(decoded, str) and accept(decoded, old): return decoded
    raise ValueError('The selected replacement does not match the bounded source correction')


def inspect_polish(rows):
    failures = set(); samples = 0
    for row in rows:
        if row.get('time', 0) < 1: continue
        samples += 1
        panels = {p['name']: p for p in row.get('routeChapter', {}).get('hudPanels', [])}
        for name in ('MissionBoard', 'HudStatus'):
            p = panels.get(name, {}); color = p.get('cardColor', [])
            if p.get('cardShader') not in ('Unlit/Color', 'Chicago/HudOpaque') or len(color) != 4 or color[3] != 1 or max(color[:3], default=1) > .15:
                failures.add(name + '-backing-not-uniform-dark-unlit')
        health = panels.get('HudStatus', {})
        displayed = re.fullmatch(r'HEALTH (\d+)\nWANTED (\d+) / 3', health.get('text', ''))
        hp = row.get('health'); pursuit = row.get('pursuit')
        if (not displayed or not isinstance(hp, (int, float)) or not math.isfinite(hp)
            or int(displayed[1]) != hp or int(displayed[2]) != pursuit):
            failures.add('health-wanted-not-actual-numeric-state')
        for key in ('textRect', 'captureTextRect'):
            box = health.get(key, [])
            if len(box) != 4 or (box[3] - box[1]) * 540 / 2 < 12:
                failures.add('status-text-too-small')
        if row.get('relay', {}).get('complete') and 'R reset' not in panels.get('MissionBoard', {}).get('text', ''):
            failures.add('completed-relay-reset-hint-missing')
    if not samples: failures.add('hud-polish-evidence-missing')
    return dict(passed=not failures, failure=sorted(failures) or None, samples=samples,
        pixel_review_required=True, final_game_accepted=False)


class HudPresentationPolish(HudLiveObjective):
    def validate_recovery(self, old):
        validate_pause(old); self.resume_capacity = False; self.priority_resume = False
        self.transport_recovery = old.get('current_round') == 'q0118-ca136f22'
        if self.transport_recovery:
            p = self.store.root / 'private/sessions/q0118-ca136f22-objective-unlit-backing/response-000.json'
            if sha(p.read_bytes()) != 'a89b0d5cf26fef8ef953af26cbcc37c03c603d11689da3b722bd35f368e6a190':
                raise Halt('Preserve the exact completed local patch submission')
        p = self.store.root / 'evidence' / ROUND / 'consolidated-hud-outcome.json'
        if sha(p.read_bytes()) != OUTCOME_SHA: raise Halt('Preserve the independent local FIX verdict')

    def wait_for_capacity(self):
        self.capacity.wait('local-hud-presentation-polish')

    def recovery_settings(self):
        return dict(hud_presentation_polish_attempted=True, hud_patch_transport_recovered=self.transport_recovery,
            recovery_route='local-verified-HUD-visual-fixes',
            recovery_change='Local opaque unlit backings, larger numeric health/wanted and completed-relay reset hint. '
            'No extra-card removal: native trace already proves old renderers disabled. Fresh native gates/images and critic; '
            'hash-identical compiled artifact reuse within this owner only, no runtime evidence reuse.')

    def patch(self, ident, label, path, old, instruction, accept, max_lines=6):
        raw = (self.project / path).read_text()
        if raw.count(old) != 1: raise Halt('Require one exact selected source span')
        first = raw[:raw.index(old)].count('\n') + 1
        edit = SelectedEdit(Files(self.project, self.store), path, first, first + len(old.splitlines()) - 1, max_lines=max_lines)
        if self.transport_recovery and label == 'objective-unlit-backing':
            p = self.store.root / 'private/sessions/q0118-ca136f22-objective-unlit-backing/response-000.json'
            response = p.read_bytes(); choice = json.loads(response)['choices'][0]
            calls = choice['message'].get('tool_calls', [])
            if choice['finish_reason'] != 'tool_calls' or len(calls) != 1 or calls[0]['function']['name'] != 'edit_selected_span':
                raise Halt('Require the complete original local source tool call')
            content = json.loads(calls[0]['function']['arguments'])['content']
            expected = 'var unlitShader = Shader.Find("Unlit/Color");\nvar boardMat = new Material(unlitShader);\nboardMat.color = new Color(0.06f, 0.07f, 0.085f, 1f);\nforeach (var r in cl.GetComponentsInChildren<Renderer>()) { r.material = boardMat; r.enabled = true; }'
            content = exact_content(content, lambda value, _: compact(value) == compact(expected), old)
            edit.apply(ident + '-recover-original-card-material', content)
            self.store.event('complete-local-hud-patch-recovered', response_sha256=sha(response),
                private_reasoning_used=False, source_authored_by='local-Qwen', one_json_transport_layer_decoded=True)
        else:
            self.c.update(output_tokens=1536, model_timeout_seconds=110)
            self.store.set(stage='local-hud-polish-' + label); self.store.report()
            result = self.model.session('builder', ident + '-' + label,
                'You are local Qwen repairing your own saved game source. Submit the exact scoped replacement.',
                instruction + '\nPreserve existing identifier names. Use real source newlines in content, not an extra JSON escaping layer. '
                'Call finish_source now.\nEXACT SELECTED SOURCE:\n' + old,
                [tool('finish_source', 'Apply this one bounded selected source replacement.', {'content': {'type': 'string'}})],
                {'finish_source': lambda action, fields: edit.apply(action, exact_content(fields['content'], accept, old))},
                turns=2, reasoning_effort='low')
            if (self.project / path).read_text() == raw:
                raise Halt('Local HUD correction not saved: ' + label + ': ' + json.dumps(result))
        candidate = self.checkpoint_source('Local Qwen: ' + label)
        self.store.set(source_checkpoint=candidate, candidate_commit=candidate)

    def source(self, ident):
        raw = (self.project / PATH).read_text()
        old = next(s for s in raw.splitlines(True) if 'foreach (var r in cl.GetComponentsInChildren<Renderer>())' in s)
        expected = 'var mat = new Material(Shader.Find("Unlit/Color"));\nmat.color = new Color(.06f,.07f,.085f,1f);\nforeach (var r in cl.GetComponentsInChildren<Renderer>()) { r.sharedMaterial = mat; r.enabled = true; }'
        self.patch(ident, 'objective-unlit-backing', PATH, old,
            'The cloned BoardCard uses scene-lit Standard material, visibly changing with street lighting. '
            'Replace only this renderer enable line with one new Unlit/Color material, opaque color(.06,.07,.085,1), '
            'then assign it to each cloned-card renderer and enable that renderer. Keep all transforms/colliders/state unchanged.',
            lambda value, _: compact(value) == compact(expected), 6)
        raw = (self.project / PATH).read_text()
        old = next(s for s in raw.splitlines(True) if 'string foot = "\\nDelivery complete / Dead-drop complete";' in s)
        self.patch(ident, 'completed-reset-hint', PATH, old,
            'Preserve this footer, then append exactly if (_relay.AllComplete) foot += "\\nR reset"; '
            'The relay writer remains unchanged; this is the fourth visible line only after actual completion.',
            lambda value, previous: compact(value) == compact(previous + 'if (_relay.AllComplete) foot += "\\nR reset";'), 3)
        raw = (self.project / STATUS).read_text()
        start = raw.index('            card.transform.localPosition =')
        end = raw.index('            card.GetComponent<Renderer>().sharedMaterial', start)
        old = raw[start:end]
        expected = old.replace('new Vector3(0.42f, -0.045f, 0.03f)', 'new Vector3(0.26f, -0.065f, 0.03f)').replace(
            'new Vector3(0.92f, 0.15f, 0.01f)', 'new Vector3(0.60f, 0.22f, 0.01f)').replace(
            'Shader.Find("Standard")', 'Shader.Find("Unlit/Color")').replace('new Color(0f, 0f, 0f, 0.72f)', 'new Color(.06f, .07f, .085f, 1f)')
        self.patch(ident, 'status-unlit-card', STATUS, old,
            'Keep this block otherwise unchanged. StatusCard localPosition(.26,-.065,.03), localScale(.60,.22,.01). '
            'Use Unlit/Color instead of Standard, color(.06,.07,.085,1) opaque. Preserve collider cleanup and real status state.',
            lambda value, _: compact(value) == compact(expected), 10)
        raw = (self.project / STATUS).read_text(); lines = raw.splitlines(True)
        index = next(i for i, s in enumerate(lines) if 'tm.fontSize = 34;' in s); old = ''.join(lines[index:index + 2])
        expected = old.replace('34', '40').replace('0.011f', '0.017f')
        self.patch(ident, 'readable-status-font', STATUS, old,
            'Increase actual health/wanted text legibility: fontSize40, characterSize0.017f. Only these two values.',
            lambda value, _: compact(value) == compact(expected), 3)
        raw = (self.project / STATUS).read_text(); start = raw.index('            string stars =')
        end = raw.index('            tm.color =', start); old = raw[start:end]
        expected = 'tm.text = "HEALTH " + hp + "\\nWANTED " + w + " / 3";'
        self.patch(ident, 'numeric-wanted-readout', STATUS, old,
            'Replace the tiny star/dot glyph assembly with the exact actual numeric readout '
            'tm.text = "HEALTH " + hp + "\\nWANTED " + w + " / 3"; '
            'Do not clamp or change hp/w, ReadInt, combat signals, health colors or refresh caching.',
            lambda value, _: compact(value) == compact(expected), 2)
        return self.store.get('source_checkpoint')

    def relay_native(self, ident, candidate, probe, case):
        bundle, gate = super().relay_native(ident, candidate, probe, case)
        path = bundle / 'captures/trace.jsonl'
        if path.exists():
            check = inspect_polish([json.loads(line) for line in path.read_text().splitlines()])
            atomic(bundle / 'hud-polish-gate.json', check)
            if not check['passed']: gate.update(passed=False, failure=check['failure'])
        return bundle, gate

    def qualify(self, ident, candidate, results=None):
        try:
            super().qualify(ident, candidate, results)
        except Halt as error:
            if str(error) != 'Consolidated HUD qualification recorded; continue corrected encounter acceptance and broad visual work':
                raise
            if not self.store.get('consolidated_hud_outcome', {}).get('accepted'):
                raise
        # The accepted HUD immediately feeds the already planned combat dependency.
        # Only local Qwen edits game code; a new source gets a new compiled artifact.
        self.store.set(stage='local-combat-hit-target-scope'); self.store.report()
        path = 'Assets/Game/Combat.cs'; raw = (self.project / path).read_text()
        start = raw.index('                    first.alive = false;')
        end = raw.index('                }', start)
        old = raw[start:end]
        expected = old.replace('rivalGo.GetComponentsInChildren<Renderer>()', 'first.GetComponentsInChildren<Renderer>()').replace(
            'rivalGo.GetComponent<CapsuleCollider>()', 'first.GetComponent<CapsuleCollider>()')
        self.patch(ident, 'actual-hit-target-death', path, old,
            'Actual HandleFire already damages the first-hit RivalAgent. Its death branch wrongly hides the '
            'original rivalGo even when a different agent was hit. Replace ONLY both rivalGo receiver uses in '
            'this selected death branch with first; preserve first.alive=false, renderer disable and capsule '
            'disable statements. No second fire handler, new targets, movement, signals or reset changes.',
            lambda value, _: compact(value) == compact(expected), 8)
        candidate = self.store.get('source_checkpoint')
        self.store.set(stage='combat-hit-target-original-regressions'); self.store.report()
        gates = self.regress(TASKS[7], ident + '-hit-target', candidate)
        atomic(self.store.root / 'evidence' / (ident + '-hit-target-result.json'),
            dict(candidate=candidate, original_regressions=gates, new_multi_target_behavior_qualified=False))
        if not gates.get('passed'): raise Halt('Hit-target scope repair changed an existing contract')
        self.store.set(combat_hit_target_preparation=dict(candidate=candidate, original_regressions_passed=True,
            new_multi_target_behavior_qualified=False))
        self.store.report()
        raise Halt('Local hit-target dependency and original regressions complete; next qualify the planned moving encounter')

    def review(self, task, ident, bundle, gate):
        checks = []
        for path in sorted((self.store.root / 'evidence').glob(ident + '-*/captures/trace.jsonl')):
            rows = [json.loads(line) for line in path.read_text().splitlines()]
            result = inspect_polish(rows); atomic(path.parent.parent / 'hud-polish-gate.json', result)
            checks.append(dict(evidence=path.parent.parent.name, **result))
        if len(checks) != 13 or not all(c['passed'] for c in checks):
            raise Halt('New HUD material/status/reset contract failed: ' + json.dumps([c for c in checks if not c['passed']]))
        atomic(bundle / 'hud-polish-regressions.json', checks)
        result = review_hud(self, ident, bundle, gate)
        atomic(bundle / 'critic.json', result)
        return result


if __name__ == '__main__': raise SystemExit(main(HudPresentationPolish))
