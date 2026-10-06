#!/usr/bin/env python3
"""Review sealed current-source HUD frames without repeating passed native tests."""
import json
from resume_hud_live_objective import HudLiveObjective, CAPACITY_SOURCE as SOURCE, ACCEPTED
from resume_consolidated_hud import TASK
from resume_three_day_queue import main
from continue_game_queue import review_captures, validate_scoped_review
from loop_controller.core import Halt, atomic, read_json, sha, verify_seal
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.model import tool

ROUND = 'q0116-0ee2b77b'
EVIDENCE = 'q0115-a478e7c8-positive'
HASHES = {'scoped-gate.json': 'c5541ae9805dc87c4560bebcebda7ec7760b7d64fcec4e3eb833862e19b5c21d',
          'captures/manifest.json': '990474055ea668caabd0096d7741eba882d211963c68f7a9e4a9044573fd89ed',
          'consolidated-hud-outcome.json': 'f5c959c92bd00b553e223157bd0fb1da4e957c80bbef700ed55f6c8f1a1f91e9'}


def validate_pause(old):
    expected = dict(source_checkpoint=SOURCE, last_playable_checkpoint=ACCEPTED, current_round=ROUND,
        task_index=7, task_failures=24, failure_streak=1, diagnosis_used=True,
        overall_deadline_epoch=HARD_CAP_EPOCH, stage='fresh-consolidated-hud-critique',
        blocker='Halt: Consolidated HUD qualification recorded; continue corrected encounter acceptance and broad visual work')
    if any(old.get(k) != v for k, v in expected.items()) or old.get('hud_bounded_review_attempted'):
        raise Halt('Require exact pre-inference HUD context stop with preserved source/history')
    if old.get('consolidated_hud_outcome', {}).get('review', {}).get('bounded_stop') != 'context':
        raise Halt('Do not retry a different critic outcome')


def focused_facts(gate):
    """Mechanics are separately verified; pass no duplicated per-sample trees to vision."""
    regs = gate.get('regressions', {}).get('regressions', [])
    hud = gate.get('hud_regressions', [])
    if (not gate.get('passed') or gate.get('candidate_commit') != SOURCE or len(regs) != 10
        or not all(x['gate'].get('passed') and x['gate'].get('candidate_commit') == SOURCE for x in regs)
        or len(hud) != 10 or not all(x['check'].get('passed') for x in hud)
        or not gate.get('consolidated_hud', {}).get('passed')):
        raise Halt('Require all current-source native mechanics and HUD regression passes')
    return dict(candidate=SOURCE, build_id=gate['build_id'], native_passed=True,
        regression_tests=[x['test'] for x in regs], hud_regression_passes=len(hud),
        progression_seconds=59.633335114, relay_seconds_included=27.100002289,
        reset_seconds=80.033332825, final_game_accepted=False,
        native_contract='Truthful live objective/receipt text, two visible panels, text/backing containment, '
        'no panel overlap, legibility geometry, live 4:3 and capture 16:9, reset and inactive/timeout paths. '
        'These mechanical checks do not substitute for independent image judgment.')


class HudBoundedReview(HudLiveObjective):
    def validate_recovery(self, old):
        validate_pause(old)
        self.resume_capacity = True
        self.priority_resume = False
        e = self.store.root / 'evidence' / EVIDENCE
        for name, digest in HASHES.items():
            if sha((e / name).read_bytes()) != digest:
                raise Halt('Preserve original HUD evidence: ' + name)
        verify_seal(e / 'captures', HASHES['captures/manifest.json'])
        focused_facts(read_json(e / 'scoped-gate.json'))
        if any((self.store.root / 'private/sessions' / (ROUND + '-critic')).iterdir()):
            raise Halt('Expected original critic to stop before any inference request')

    def wait_for_capacity(self):
        self.capacity.wait('local-hud-visual-review')

    def recovery_settings(self):
        return dict(hud_bounded_review_attempted=True, recovery_route='sealed-HUD-focused-critic',
            recovery_change='Retain four original native images and all native checks; remove duplicated '
            'per-sample diagnostic trees from the critic prompt. Preserve context/output limits and original rejection.')

    def work(self):
        ident = self.begin(TASK, 'fresh-bounded-hud-critique')
        original = self.store.root / 'evidence' / EVIDENCE
        gate = read_json(original / 'scoped-gate.json')
        facts = focused_facts(gate)
        chosen, times = review_captures(TASK, original)
        names = [p.name for p in chosen]
        self.c.update(output_tokens=8192, model_timeout_seconds=400)
        review = self.model.session('critic', ident + '-critic',
            'You are a fresh local visual critic. Judge the supplied actual game frames independently.',
            'SCOPE: consolidated mission HUD only. One readable MissionBoard objective plus separate health/wanted. '
            'Old overlapping delivery/cache/relay cards should be absent; actual stage, next action, distance, '
            'control and compact completed-stage receipts should be readable and truthful. Check the four images '
            'for clipping, overlap, unreadable text or blocking HUD regressions. Mechanical PASS is not visual PASS. '
            'Character, window, street art and ten-minute pacing remain unresolved outside this HUD scope. '
            'No reference-quality or final-game claim. Cite actual supplied frame filenames and scheduled times. '
            'Return PASS, FIX, or UNVERIFIED via submit_review; for FIX/UNVERIFIED give 3-5 prioritized concrete fixes. '
            'Do not infer unshown details or invent timing.\nVERIFIED MECHANICS:' + json.dumps(facts) +
            '\nAUTHORITATIVE FRAME TIMES:' + json.dumps(times),
            [tool('submit_review', 'Return the independent scoped HUD verdict.',
                {'verdict': {'type': 'string', 'enum': ['PASS', 'FIX', 'UNVERIFIED']},
                 'summary': {'type': 'string'}, 'fixes': {'type': 'array', 'items': {'type': 'string'}}})],
            {'submit_review': lambda _, f: validate_scoped_review(f, names, times)},
            images=[('ACTUAL NATIVE UNITY ' + p.name + '; scheduled t=' + str(times[p.name]) + 's', p) for p in chosen],
            turns=3, reasoning_effort='xhigh')
        verify_seal(original / 'captures', HASHES['captures/manifest.json'])
        e = self.store.root / 'evidence' / ident
        e.mkdir(exist_ok=True)
        outcome = dict(candidate=SOURCE, evidence=str(original.relative_to(self.store.root)),
            review=review, accepted=bool(review.get('ok') and review.get('verdict') == 'PASS'),
            final_game_accepted=False, original_context_rejection_preserved=True, native_rerun=False)
        atomic(e / 'consolidated-hud-outcome.json', outcome)
        atomic(e / 'evidence-reuse.json', dict(original=EVIDENCE, hashes=HASHES, facts=facts))
        self.store.set(consolidated_hud_outcome=outcome)
        self.store.report()
        raise Halt('Focused HUD review recorded; continue measured local gameplay and visual work')


if __name__ == '__main__':
    raise SystemExit(main(HudBoundedReview))
