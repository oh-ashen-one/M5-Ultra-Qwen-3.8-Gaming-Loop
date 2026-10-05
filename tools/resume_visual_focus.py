#!/usr/bin/env python3
"""One image-led original-asset improvement inside the existing Chicago queue."""
import json
import time
import uuid

from continue_game_queue import ContinuousRunner, ReadBoundEdits, validate_scoped_review
from resume_three_day_queue import ThreeDayRunner, main
from loop_controller.core import Files, Halt, atomic, now, read_json, seal, sha, verify_seal
from loop_controller.continuous_tasks import TASKS
from loop_controller.delivery_policy import HARD_CAP_EPOCH, queue_milestone
from loop_controller.model import tool
from loop_controller.review_summary import critic_evidence
from loop_controller.runner import git
from loop_controller.small_edits import SelectedEdit

SOURCE = '137d0d2354b121da51e91c3cc128a689ed440fab'
ACCEPTED = '102a2095b13f29e9df24f7061691b9a5c194a896'
S = {'type': 'string'}
ASSETS = ['Art/' + n + '.py' for n in ('street', 'coupe', 'props', 'player')]


def validate_visual_pause(old):
    expected = dict(source_checkpoint=SOURCE, last_playable_checkpoint=ACCEPTED, task_index=7,
        task_failures=2, failure_streak=1, diagnosis_used=False,
        overall_deadline_epoch=HARD_CAP_EPOCH, blocker='Halt: Requested stop')
    if any(old.get(k) != v for k, v in expected.items()) or old.get('visual_focus_attempted'):
        raise Halt('Expected the exact parent-directed q0038 visual-phase pause')


def changed_span(current, accepted):
    """Find the smallest whole-line span needed to restore accepted local source."""
    a, b = current.splitlines(keepends=True), accepted.splitlines(keepends=True)
    start = 0
    while start < min(len(a), len(b)) and a[start] == b[start]: start += 1
    if start == len(a) == len(b): return None
    suffix = 0
    while suffix < min(len(a), len(b)) - start and a[-1-suffix] == b[-1-suffix]: suffix += 1
    end = len(a) - suffix
    if end <= start: raise Halt('Expected an actual changed source span')
    return start + 1, end, ''.join(b[start:len(b)-suffix if suffix else len(b)])


class VisualFocusResume(ThreeDayRunner):
    before_evidence = 'evidence/q0037-9ec6dbea/captures/frame-000.png'
    def validate_recovery(self, old): validate_visual_pause(old)
    def recovery_settings(self): return {'visual_focus_attempted': True}

    def restore_mechanics(self, ident):
        files = Files(self.project, self.store)
        for name in ('Combat.cs', 'Mission.cs'):
            path = 'Assets/Game/' + name
            accepted = git(self.repo, 'show', ACCEPTED + ':game/' + path) + '\n'
            current = files.path(path).read_text()
            change = changed_span(current, accepted)
            if change is None: continue
            start, end, replacement = change
            edit = SelectedEdit(files, path, start, end, max_lines=140)
            self.c.update(output_tokens=4096, model_timeout_seconds=240)
            def restore(action, fields):
                if fields['content'].rstrip() != replacement.rstrip():
                    raise ValueError('Restore the supplied accepted span exactly; do not redesign mechanics')
                return edit.apply(action, fields['content'])
            self.store.set(stage='preserve-accepted-mechanics'); self.store.report()
            self.model.session('builder', ident + '-restore-' + name,
                'You are local Qwen preserving your previously accepted game mechanics before art work.',
                'Later unaccepted edits widened the aim cone or changed delivery behavior while compensating for a bad replay. '
                'Restore this exact span from your accepted checkpoint102a2095. The original later commits stay preserved. '
                'Call edit_selected_span with the supplied accepted content. No new design.\nPATH:' + path +
                '\nCURRENT SPAN:\n' + edit.old + '\nACCEPTED REPLACEMENT:\n' + replacement,
                [tool('edit_selected_span', 'Restore this accepted source span.', {'content': S})],
                {'edit_selected_span': restore}, turns=1, reasoning_effort='low')
            if files.path(path).read_text().rstrip() != accepted.rstrip():
                raise Halt('Accepted mechanics restoration incomplete: ' + name)
        saved = self.checkpoint_source('Local Qwen: preserve accepted mechanics before image-led art work')
        self.store.set(source_checkpoint=saved)

    def choose_focus(self, ident, before):
        self.c.update(output_tokens=8192, model_timeout_seconds=400)
        def submit(_, fields):
            if 'before.png' not in fields['decision'] or len(fields['decision']) > 3000:
                raise ValueError('Cite before.png and keep the single-gap decision concise')
            return {'ok': True, **fields}
        self.store.set(stage='fresh-visual-gap-selection'); self.store.report()
        result = self.model.session('visual-planner', ident + '-visual-plan',
            'You are a fresh local Qwen art critic selecting one bounded visible improvement.',
            'Compare the ACTUAL before.png with the Chicago reference. Lighting became warmer but the geometry and '
            'surroundings are still crude and empty. Identify the single largest visible gap you can improve by revising '
            'ONE existing original Blender script, then state the concrete geometry/composition change and what the next '
            'like-for-like native frame must show. Lighting-only recoloring is not substantial progress. Keep the existing '
            'camera, actor scale, mission markers, collider-bearing geometry, pavement and route unchanged in this first pass. '
            'You may add detail or decorative street context within the selected existing asset; no new asset pack/script. '
            'No gameplay or target-hit changes. Select only one of the offered existing scripts. At most200 words. '
            'Call submit_plan now; do not ask for broad source exploration.',
            [tool('submit_plan', 'Choose one largest visible gap and existing asset.',
                  {'asset': {'type': 'string', 'enum': ASSETS}, 'decision': S})],
            {'submit_plan': submit}, images=[('before.png ACTUAL q0037 native frame', before),
                ('Chicago target reference, not game output', self.refs/'chicago_01_neighborhood_on_foot.png')],
            turns=2, reasoning_effort='xhigh')
        if not result.get('ok'): raise Halt('Visual gap selection incomplete; preserve evidence')
        self.store.set(visual_focus=result); self.store.event('local-visual-focus', **result)
        return result

    def improve_asset(self, ident, focus, before):
        files = Files(self.project, self.store); edits = ReadBoundEdits(files, polish=True)
        selected = focus['asset']; original = sha(files.path(selected).read_bytes()); exported = {}
        csharp = {str(p.relative_to(self.project)): sha(p.read_bytes()) for p in (self.project/'Assets/Game').glob('*.cs')}
        def replace(action, fields):
            if fields['path'] != selected: raise ValueError('This bounded visual step edits only ' + selected)
            return edits.replace(action, fields)
        def export(action, _):
            digest = sha(files.path(selected).read_bytes())
            if digest == original: raise ValueError('Save the selected geometry improvement before exporting')
            result = self.engines.blender(self.project, selected, action)
            if result.get('ok'): exported['sha256'] = digest
            return result
        def finish(_, fields):
            if exported.get('sha256') != sha(files.path(selected).read_bytes()):
                raise ValueError('Export the latest saved asset through run_blender before finishing')
            return {'ok': True, **fields}
        self.c.update(output_tokens=8192, model_timeout_seconds=400)
        self.store.set(stage='local-focused-blender-author'); self.store.report()
        result = self.model.session('builder', ident + '-art-builder',
            'You are the sole local Qwen original Blender author. Implement one concrete image-led improvement.',
            'FOCUS:' + json.dumps(focus) + '\nRead the selected current script, make one compact saved change, export it, '
            'then finish. No new file or asset volume. Preserve existing root basis, meshes carrying colliders, pavement, '
            'spawn, camera and gameplay. Added decorative geometry must not obstruct the accepted route. No packages or '
            'downloaded assets. Aim for a substantial visible architectural/context improvement, not just colors. '
            'Keep meshes/export below50MiB each and avoid thousands of separate tiny objects. Existing scene placement:\n' +
            files.path('Assets/Game/Bootstrap.cs').read_text() + '\nSelected script is ' + selected +
            '. Use only offered tools, one call at a time; save promptly. read_file returns total_lines.',
            [tool('read_file', 'Read exact current source.', {'path': S, 'start_line': {'type': 'integer'}, 'line_count': {'type': 'integer'}}, ['path']),
             tool('replace_text', 'Edit only the selected existing original art script.', {'path': S, 'old': S, 'new': S}),
             tool('run_blender', 'Export the selected original asset through the protected Blender adapter.', {}),
             tool('finish_task', 'Finish after saving and exporting the selected change.', {'summary': S})],
            {'read_file': edits.read, 'replace_text': replace, 'run_blender': export, 'finish_task': finish},
            images=[('before.png ACTUAL game', before), ('Chicago target, not game output', self.refs/'chicago_01_neighborhood_on_foot.png')],
            turns=10, reasoning_effort='low')
        if any(sha(files.path(p).read_bytes()) != digest for p, digest in csharp.items()):
            raise Halt('Visual-only step unexpectedly changed gameplay source')
        if not result.get('ok') or exported.get('sha256') != sha(files.path(selected).read_bytes()):
            raise Halt('Focused Blender work remains incomplete; preserve saved source and exports')
        return result

    def work(self):
        ident = 'v%04d-%s' % (self.store.get('rounds', 0) + 1, uuid.uuid4().hex[:8])
        self.store.set(current_round=ident, rounds=self.store.get('rounds', 0)+1,
                       current_task='One image-led original Blender improvement; preserve integrated mechanics')
        before = self.store.root/self.before_evidence
        self.restore_mechanics(ident)
        focus = self.choose_focus(ident, before)
        self.improve_asset(ident, focus, before)
        candidate = self.checkpoint_source('Local Qwen: image-led ' + focus['asset'] + ' improvement')
        self.store.set(source_checkpoint=candidate, stage='native-visual-comparison'); self.store.report()
        probe = read_json(self.store.root/'evidence/q0035-e5f1e32d/captures/scenario.json')
        bundle, gate = ContinuousRunner.native(self, TASKS[6], ident, candidate, probe)
        if not gate.get('passed'): raise Halt('Focused visual candidate regressed the integrated route; preserve evidence')
        self.store.set(stage='visual-mechanics-regressions'); self.store.report()
        regression = self.regress(TASKS[6], ident, candidate); gate['regressions'] = regression
        if not regression['passed']: gate.update(passed=False, failure=regression['failure'])
        atomic(bundle/'scoped-gate.json', gate)
        if not gate['passed']: raise Halt('Focused visual candidate regressed accepted mechanics; preserve evidence')
        self.c.update(output_tokens=8192, model_timeout_seconds=400)
        captures = bundle/'captures'; digest = seal(captures, {'candidate': candidate, 'scope': 'visual-improvement'})
        self.store.set(stage='fresh-visual-comparison'); self.store.report()
        review = self.model.session('critic', ident + '-visual-critic',
            'You are a fresh local visual critic. A meaningful geometry/composition improvement is required.',
            'Judge the specific chosen gap: ' + json.dumps(focus) + '. Compare before.png and after.png at the same '
            'stationary spawn camera, then assess drive.png. Require a clearly visible improvement beyond lighting/color '
            'and no blocking regression. A PASS accepts this bounded improvement only; ten-minute pacing and final Chicago '
            'quality remain unaccepted. Cite actual frame names. Give up to five next visible fixes.\nNATIVE:' +
            json.dumps(critic_evidence(gate)),
            [tool('submit_review', 'Return evidence-based visual improvement verdict.',
                  {'verdict': {'type': 'string', 'enum': ['PASS', 'FIX', 'UNVERIFIED']}, 'summary': S,
                   'fixes': {'type': 'array', 'items': S}})],
            {'submit_review': lambda _, f: validate_scoped_review(f, ['before.png', 'after.png', 'drive.png'])},
            images=[('before.png ACTUAL prior native spawn view, '+self.before_evidence, before), ('after.png ACTUAL current build, t3.2', captures/'frame-000.png'),
                    ('drive.png ACTUAL current build, t15.5', captures/'frame-005.png'),
                    ('Chicago target reference, not game output', self.refs/'chicago_01_neighborhood_on_foot.png')],
            turns=2, reasoning_effort='xhigh')
        verify_seal(captures, digest); atomic(bundle/'visual-critic.json', review)
        self.store.set(visual_focus_review=review)
        if not review.get('ok') or review.get('verdict') != 'PASS':
            raise Halt('Focused visual improvement not accepted; preserve exact images and local criticism')
        record = dict(candidate=candidate, accepted_utc=now(), focus=focus, review=review,
                      evidence=str(bundle.relative_to(self.store.root)), final_game_accepted=False)
        path = self.project/'Notes'/('visual-' + ident + '.json'); atomic(path, record)
        git(self.repo, 'add', '--', str(path.relative_to(self.repo)))
        git(self.repo, '-c', 'user.name=Evidence controller', '-c', 'user.email=254017794+oh-ashen-one@users.noreply.github.com',
            'commit', '-m', 'Record bounded original-asset visual improvement; final game remains pending')
        saved = git(self.repo, 'rev-parse', 'HEAD')
        self.store.set(last_playable_checkpoint=saved, source_checkpoint=saved,
            last_verified_progress_epoch=time.time(), last_verified_progress_utc=now(),
            latest_visual_milestone=record, feedback={'visual_focus': focus, 'visual_review': review,
                'route_instruction': 'Preserve accepted thin-ray combat and delivery. Prioritize substantial remaining Chicago geometry/composition and meaningful ten-minute pacing; never widen hit logic to compensate for a bad replay.'})
        visual_task = {**TASKS[6], 'id': 'original-asset-visual-improvement', 'outcome': focus['decision']}
        frames = [captures/'frame-000.png', captures/'frame-005.png']
        queue_milestone(self.store, 'accepted-feature', visual_task, bundle, gate, frames,
                        {'frame-000.png': 3.2, 'frame-005.png': 15.5}, review)
        self.store.event('visual-improvement-accepted', **record, checkpoint=saved, original_task_failure_counts_preserved=True)
        self.store.report()
        return super().work()


if __name__ == '__main__': raise SystemExit(main(VisualFocusResume))
