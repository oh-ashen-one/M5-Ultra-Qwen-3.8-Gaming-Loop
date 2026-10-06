#!/usr/bin/env python3
"""Revalidate numeric display equivalence against preserved completed native evidence."""
import json
import shutil
import tempfile
from pathlib import Path
from resume_hud_shader_recovery import HudShaderRecovery
from resume_hud_presentation_polish import inspect_polish
from resume_hud_live_objective import ACCEPTED
from resume_consolidated_hud import TASK
from resume_three_day_queue import main
from loop_controller.core import Halt, atomic, read_json, sha
from loop_controller.adapters import encode_directory
from loop_controller.build_reuse import build_key
from loop_controller.consolidated_hud import inspect_hud
from loop_controller.delivery_policy import HARD_CAP_EPOCH

SOURCE = 'c36a313ae5eb3b6733eff411a1cd1b3504706ae0'
ROUND = 'q0120-dc4867c8'


def validate_pause(old):
    expected = dict(source_checkpoint=SOURCE, last_playable_checkpoint=ACCEPTED, current_round=ROUND,
        task_index=7, task_failures=24, failure_streak=1, diagnosis_used=True,
        overall_deadline_epoch=HARD_CAP_EPOCH, stage='native-consolidated-hud-positive',
        blocker='Halt: Consolidated HUD positive needs measured diagnosis: ["health-wanted-not-actual-numeric-state"]')
    if any(old.get(k) != v for k, v in expected.items()) or old.get('hud_numeric_evidence_recovered'):
        raise Halt('Require exact numeric-format validator failure with unchanged source/history')


class HudNumericEvidence(HudShaderRecovery):
    def original(self):
        return self.store.root / 'evidence' / (ROUND + '-positive')

    def validate_recovery(self, old):
        validate_pause(old)
        self.resume_capacity = False; self.priority_resume = False; self.transport_recovery = False
        e = self.original(); raw = read_json(e / 'gate.json'); relay = read_json(e / 'relay-gate.json')
        failed = read_json(e / 'consolidated-hud-gate.json')
        if (not raw.get('passed') or not relay.get('passed') or raw.get('candidate_commit') != SOURCE
            or relay.get('candidate_commit') != SOURCE or failed.get('failure') != ['health-wanted-not-actual-numeric-state']):
            raise Halt('Do not reinterpret a failed runtime or different native failure')
        if sha(encode_directory(e / 'build/ChicagoLocalSlice.app')) != raw['build_id']:
            raise Halt('Original completed native binary changed')
        rows = [json.loads(line) for line in (e / 'captures/trace.jsonl').read_text().splitlines()]
        if not inspect_polish(rows)['passed'] or not inspect_hud(rows, ['grab','carrying','dead-drop','relay','relay-complete'])['passed']:
            raise Halt('Correct numeric comparison must pass every original display/state sample')
        # Reconstruct the exact pre-import source+asset+harness tree before admitting
        # this explicitly reviewed prior binary to the new owner's ephemeral cache.
        with tempfile.TemporaryDirectory(prefix='hud-source-identity-', dir=self.store.root) as td:
            prepared = Path(td) / 'project'; shutil.copytree(self.project, prepared)
            shutil.copytree(self.engines.source_root / 'controller/unity', prepared / 'Assets/LoopHarness')
            if build_key(prepared, self.c['unity'], SOURCE) != raw.get('build_input_sha256'):
                raise Halt('Current source, assets, harness or editor differ from the completed native build')
        self.proof_hashes = {name: sha((e / name).read_bytes()) for name in
            ['gate.json','relay-gate.json','consolidated-hud-gate.json','hud-polish-gate.json','captures/trace.jsonl','captures/runtime-result.json']}

    def recovery_settings(self):
        return dict(hud_numeric_evidence_recovered=True, recovery_route='numeric-equivalence-native-evidence-revalidation',
            recovery_change='Observer health is float; HUD reads the same integer state. Compare parsed values exactly '
            'instead of requiring a .0 suffix. Preserve original failure. Explicitly reuse only validated same-input '
            'binary and completed positive evidence; all remaining scenarios run fresh.')

    def work(self):
        ident = self.begin(TASK, 'revalidate-hud-numeric-display')
        original = self.original(); bundle = self.store.root / 'evidence' / (ident + '-positive')
        bundle.mkdir()
        for name, digest in self.proof_hashes.items():
            if sha((original / name).read_bytes()) != digest: raise Halt('Original numeric rejection evidence changed')
        shutil.copytree(original / 'captures', bundle / 'captures')
        shutil.copytree(original / 'build', bundle / 'build', symlinks=True)
        rows = [json.loads(line) for line in (bundle / 'captures/trace.jsonl').read_text().splitlines()]
        gate = read_json(original / 'relay-gate.json')
        gate['consolidated_hud'] = inspect_hud(rows, ['grab','carrying','dead-drop','relay','relay-complete'])
        gate['hud_polish'] = inspect_polish(rows)
        gate['evidence_revalidation'] = dict(original=original.name, original_failure_preserved=True,
            fresh_runtime=False, interpretation_change='Exact numeric equivalence, no tolerance or health rounding')
        atomic(bundle / 'consolidated-hud-gate.json', gate)
        atomic(bundle / 'hud-polish-gate.json', gate['hud_polish'])
        atomic(bundle / 'gate.json', read_json(original / 'gate.json'))
        atomic(bundle / 'evidence-reuse.json', dict(original=original.name, hashes=self.proof_hashes,
            native_rerun=False, image_bytes_unchanged=True))
        raw = read_json(original / 'gate.json')
        self.engines.build_reuse.remember(raw['build_input_sha256'], original / 'build')
        self.qualify(ident, SOURCE, {'positive': dict(evidence=str(bundle.relative_to(self.store.root)), passed=True)})


if __name__ == '__main__': raise SystemExit(main(HudNumericEvidence))
