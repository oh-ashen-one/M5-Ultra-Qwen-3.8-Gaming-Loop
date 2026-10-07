"""Reuse protected native inputs for original-asset edits; never accept final pacing."""
import json
import re
import time
from pathlib import Path

from loop_controller.core import Halt, atomic, now, read_json, seal, sha, verify_seal
from loop_controller.continuous_checks import validate_proposed
from loop_controller.continuous_tasks import TASKS
from loop_controller.model import tool
from loop_controller.review_summary import critic_evidence, require_combat_contracts
from loop_controller.aim_checks import require_aim_contracts
from loop_controller.delivery_policy import queue_milestone
from loop_controller.runner import git

ASSETS = ('street', 'coupe', 'props', 'player')
SEED_EVIDENCE = 'evidence/v0040-e9347baf'
SEED_MANIFEST = 'c35dcd247f7f7fc32faecdad9031445bdc112606349011e4c5e5be9428b11c0c'
SCENARIO_SHA = '4c378925516fda3bef07b0bb015c2a73567a420ad928fba2449a42af43721915'
ORIGINAL_REPLAY = 'evidence/q0035-e5f1e32d/captures/scenario.json'
REGRESSIONS = {'walk', 'world', 'motor', 'courier', 'failure-retry', 'combat-foot',
               'combat-wall', 'combat-driving', 'aim-miss', 'aim-near-cover'}
NEXT_FOCUS = (
    'Choose the single largest remaining visible problem from the actual frames. '
    'Prioritize courier anatomy/animation, substantial Chicago street context and lighting, '
    'then meaningful connected mission objectives and ten-minute pacing. The beacon and camera '
    'have a preserved bounded acceptance; do not reopen that edit loop or move the car lane '
    'because an image critic suggests it. Record remaining framing limits for a separately '
    'scoped representative check. Do not spend another pass adding windows or minor trim. '
    'Preserve accepted camera behavior, thin-ray combat, objective anchors, boarding, controls and physical route. '
    'All substantive game/art edits remain local Qwen. Final Chicago quality and '
    'meaningful ten-minute pacing remain separate, unaccepted goals.')


def asset_only_changes(paths):
    """Conservative structural guard: C#, cameras, scenes and settings never qualify."""
    paths = set(paths)
    names = [n for n in ASSETS if 'game/Art/' + n + '.py' in paths]
    allowed = set()
    for name in names:
        allowed.update(('game/Art/' + name + '.py',
                        'game/ArtSources/' + name + '/source.blend',
                        'game/ArtSources/' + name + '/provenance.json',
                        'game/Assets/Resources/Generated/' + name + '/scene.fbx'))
    return names if names and paths <= allowed else []


def validate_exports(project, names):
    for name in names:
        script = 'Art/' + name + '.py'
        p = project / ('ArtSources/' + name + '/provenance.json')
        if p.is_symlink() or (project / script).is_symlink():
            raise Halt('Visual authoring/provenance cannot be a symlink')
        record = read_json(p)
        if record.get('author') != 'local-Qwen' or record.get('script') != script:
            raise Halt('Missing local-Qwen export provenance')
        if record.get('script_sha256') != sha((project / script).read_bytes()):
            raise Halt('Visual authoring script changed after its export')
        entries = {x['path']: x['sha256'] for x in record.get('files', [])}
        for path in ('ArtSources/' + name + '/source.blend',
                     'Assets/Resources/Generated/' + name + '/scene.fbx'):
            target = project / path
            if target.is_symlink() or entries.get(path) != sha(target.read_bytes()):
                raise Halt('Visual export bytes differ from local-Qwen provenance')


def accepted_fixture(runner, record):
    evidence = record.get('evidence', '')
    if not re.fullmatch(r'evidence/[qv]\d{4}-[a-f0-9]{8}', evidence):
        raise Halt('Expected protected accepted visual evidence')
    accepted = runner.store.get('last_playable_checkpoint')
    note = 'game/Notes/visual-' + Path(evidence).name + '.json'
    if json.loads(git(runner.repo, 'show', accepted + ':' + note)) != record:
        raise Halt('Accepted visual record does not match its immutable Git note')
    # The note commit must describe this exact accepted game tree.
    changed = git(runner.repo, 'diff', '--name-only', record['candidate'], accepted).splitlines()
    if any(not p.startswith('game/Notes/') for p in changed):
        raise Halt('Accepted visual note is stale for the current playable source')
    captures = runner.store.root / evidence / 'captures'
    expected = record.get('capture_manifest_sha256')
    if not expected and evidence == SEED_EVIDENCE:expected = SEED_MANIFEST
    if not expected:raise Halt('Accepted comparison lacks a pinned capture manifest')
    manifest = verify_seal(captures, expected)
    if manifest.get('candidate') != record['candidate']:
        raise Halt('Accepted capture manifest source mismatch')
    scenario = captures / 'scenario.json'
    if sha(scenario.read_bytes()) != SCENARIO_SHA:
        raise Halt('Accepted immutable route or camera schedule changed')
    if sha((runner.store.root / ORIGINAL_REPLAY).read_bytes()) != SCENARIO_SHA:
        raise Halt('Original integrated replay provenance changed')
    gate = read_json(captures.parent / 'scoped-gate.json')
    tests = gate.get('regressions', {}).get('regressions', [])
    if (not gate.get('passed') or gate.get('candidate_commit') != record['candidate']
            or not gate.get('regressions', {}).get('passed')
            or {x['test'] for x in tests} != REGRESSIONS
            or not all(x['gate'].get('passed') for x in tests)):
        raise Halt('Accepted fixture lacks all real current-source mechanics checks')
    review = read_json(captures.parent / 'visual-critic.json')
    if review != record['review'] or not review.get('ok') or review.get('verdict') != 'PASS':
        raise Halt('Accepted fixture visual verdict mismatch')
    probe = validate_proposed(read_json(scenario), TASKS[6]['maximum'], TASKS[6]['coverage'])
    return captures, expected, probe


def accepted_visual_images(runner, record):
    captures, _, _ = accepted_fixture(runner, record)
    return [('ACTUAL accepted game ' + record['candidate'][:8] + ', spawn t3.2', captures / 'frame-000.png'),
            ('ACTUAL accepted game ' + record['candidate'][:8] + ', drive t15.5', captures / 'frame-005.png')]


def verify_completed_native(bundle, candidate, probe, receipt):
    """Reuse only pinned complete evidence for identical source and normal inputs."""
    from loop_controller.adapters import encode_directory, evaluate_runtime
    gate_path = bundle / 'scoped-gate.json'
    if gate_path.is_symlink() or sha(gate_path.read_bytes()) != receipt['gate_sha256']:
        raise Halt('Completed native gate changed')
    gate = read_json(gate_path)
    manifest = verify_seal(bundle / 'captures', receipt['capture_manifest_sha256'])
    if (manifest.get('candidate') != candidate or gate.get('candidate_commit') != candidate
            or not gate.get('passed') or gate.get('build_exit') != 0 or gate.get('player_exit') != 0
            or gate.get('acceptance_fixture') or gate.get('capture_id') != bundle.name
            or gate.get('build_id') != receipt['build_id']
            or read_json(bundle / 'captures/scenario.json') != probe):
        raise Halt('Completed native source, inputs, build or result mismatch')
    if sha(encode_directory(bundle / 'build/ChicagoLocalSlice.app')) != receipt['build_id']:
        raise Halt('Completed native build bytes changed')
    runtime = evaluate_runtime(bundle / 'captures', probe, gate['player_exit'], bundle.name)
    if not runtime.get('passed'):
        raise Halt('Completed native evidence no longer satisfies runtime acceptance')
    return gate


def qualify_saved_visual_candidate(runner, task, ident, candidate, *, completed_native=None):
    """Return True only when this attempt was handled as a scoped visual pass/failure."""
    if task.get('id') != 'chicago-polish-whole-route':return False
    # The old fixed corridor replay is not a comparison fixture for an expanded map.
    if runner.store.get('accepted_map_extension'):return False
    accepted = runner.store.get('last_playable_checkpoint')
    changed = git(runner.repo, 'diff', '--name-only', accepted, candidate).splitlines()
    names = asset_only_changes(changed)
    if not names:return False
    if git(runner.repo, 'rev-parse', 'HEAD') != candidate or git(runner.repo, 'status', '--porcelain'):
        raise Halt('Preserve unsaved changes before visual replay reuse')
    validate_exports(runner.project, names)
    record = runner.store.get('latest_visual_milestone', {})
    before, before_seal, probe = accepted_fixture(runner, record)
    bundle = runner.store.root / 'evidence' / ident
    if bundle.exists() and completed_native is None:
        raise Halt('Preserve existing native evidence; never overwrite a replay attempt')
    if completed_native is not None:
        gate = verify_completed_native(bundle, candidate, probe, completed_native)
    provenance = dict(reuse_kind='immutable accepted input/camera reuse',
        source_evidence=record['evidence'], original_replay=ORIGINAL_REPLAY,
        accepted_checkpoint=accepted, accepted_candidate=record['candidate'],
        scenario_sha256=SCENARIO_SHA, source_manifest_sha256=before_seal,
        candidate=candidate, changed_paths=changed, game_authorship='local Qwen',
        reuse_author='cloud controller infrastructure', final_game_accepted=False)
    atomic(runner.store.root / 'replay-reuse' / (ident + '.json'), provenance)
    runner.store.event('reuse-accepted-visual-replay', **provenance)
    runner.store.set(stage='native-visual-comparison', last_valid_replay=probe,
                     current_visual_replay=provenance)
    runner.store.report()
    from continue_game_queue import ContinuousRunner, validate_scoped_review
    if completed_native is None:
        bundle, gate = ContinuousRunner.native(runner, TASKS[6], ident, candidate, probe)
    gate['replay_reuse'] = provenance
    if gate.get('passed'):
        runner.store.set(stage='visual-mechanics-regressions');runner.store.report()
        regression = runner.regress(TASKS[6], ident, candidate)
        gate['regressions'] = regression
        if not regression['passed']:gate.update(passed=False, failure=regression['failure'])
    atomic(bundle / 'scoped-gate.json', gate)
    if not gate.get('passed'):
        runner.reject_scoped(task, ident, gate, candidate)
        return True
    if not require_combat_contracts(gate) or not require_aim_contracts(gate):
        raise Halt('Visual promotion requires every accepted combat/aim contract')
    captures = bundle / 'captures'
    digest = (completed_native['capture_manifest_sha256'] if completed_native is not None
              else seal(captures, {'candidate': candidate, 'scope': 'visual-improvement'}))
    runner.store.set(stage='fresh-visual-comparison', latest_evidence=str(bundle.relative_to(runner.store.root)))
    runner.store.report();runner.c.update(output_tokens=8192, model_timeout_seconds=400)
    review = runner.model.session('critic', ident + '-visual-critic',
        'You are a fresh local visual critic. Judge actual before/after pixels and only the bounded improvement.',
        'Compare before.png and after.png at the identical t3.2 spawn camera. The current edit changed only '
        + ', '.join('Art/' + n + '.py and its exports' for n in names) + '. Require a visible meaningful '
        'improvement beyond recoloring or invisible extra detail. Assess drive.png at t15.5 for composition '
        'and obstruction. The exact original accepted normal-input replay was reused; no new replay was '
        'authored and native/current-source regressions still had to pass. A PASS accepts this bounded '
        'improvement only, never final Chicago quality or ten-minute pacing. Cite actual frame names. '
        + NEXT_FOCUS + ' Return three to five prioritized next fixes, with the largest visible gap first. '
        'Do not keep prioritizing facade windows over the obstructed camera/car or crude actors.\nNATIVE:'
        + json.dumps(critic_evidence(gate)),
        [tool('submit_review', 'Return an actual-image verdict and prioritized next visible fixes.',
              {'verdict': {'type': 'string', 'enum': ['PASS', 'FIX', 'UNVERIFIED']},
               'summary': {'type': 'string'}, 'fixes': {'type': 'array', 'items': {'type': 'string'}}})],
        {'submit_review': lambda _, f: validate_scoped_review(f, ['before.png', 'after.png', 'drive.png'])},
        images=[('before.png ACTUAL accepted source, t3.2', before / 'frame-000.png'),
                ('after.png ACTUAL current candidate, t3.2', captures / 'frame-000.png'),
                ('drive.png ACTUAL current candidate, t15.5', captures / 'frame-005.png'),
                ('Chicago target reference, not game output', runner.refs / 'chicago_01_neighborhood_on_foot.png')],
        turns=2, reasoning_effort='xhigh')
    verify_seal(before, before_seal);verify_seal(captures, digest)
    atomic(bundle / 'visual-critic.json', review)
    runner.store.set(visual_focus_review=review)
    if not review.get('ok') or review.get('verdict') != 'PASS':
        runner.reject_scoped(task, ident, review, candidate)
        return True
    focus = dict(assets=['Art/' + n + '.py' for n in names],
                 decision='Qualify saved original-asset changes with identical accepted route and camera points')
    milestone = dict(candidate=candidate, accepted_utc=now(), focus=focus, review=review,
        evidence=str(bundle.relative_to(runner.store.root)), capture_manifest_sha256=digest,
        replay_reuse=provenance, final_game_accepted=False)
    path = runner.project / 'Notes' / ('visual-' + ident + '.json')
    atomic(path, milestone);git(runner.repo, 'add', '--', str(path.relative_to(runner.repo)))
    git(runner.repo, '-c', 'user.name=Evidence controller',
        '-c', 'user.email=254017794+oh-ashen-one@users.noreply.github.com', 'commit', '-m',
        'Record bounded visual PASS with accepted replay reuse; final game remains pending')
    saved = git(runner.repo, 'rev-parse', 'HEAD')
    runner.store.set(last_playable_checkpoint=saved, source_checkpoint=saved,
        last_verified_progress_epoch=time.time(), last_verified_progress_utc=now(),
        latest_visual_milestone=milestone, task_design=NEXT_FOCUS,
        feedback={'visual_review': review, 'next_visible_focus': NEXT_FOCUS})
    # Deliberately preserve task_index, task_failures, failure_streak and diagnosis_used.
    visual_task = {**TASKS[6], 'id': 'original-asset-visual-improvement', 'outcome': focus['decision']}
    queue_milestone(runner.store, 'accepted-feature', visual_task, bundle, gate,
        [captures / 'frame-000.png', captures / 'frame-005.png'],
        {'frame-000.png': 3.2, 'frame-005.png': 15.5}, review)
    runner.store.event('visual-replay-improvement-accepted', candidate=candidate, checkpoint=saved,
                       original_failure_counts_preserved=True, final_game_accepted=False)
    runner.store.report()
    return True
