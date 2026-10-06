#!/usr/bin/env python3
"""Close the inert q0049 camera attempt and continue one original courier asset."""
import ast
import uuid

from continue_game_queue import ContinuousRunner
from resume_three_day_queue import ThreeDayRunner, main
from resume_coupe_export import export_saved_asset
from qualify_visual_replay import accepted_fixture, qualify_saved_visual_candidate, NEXT_FOCUS
from loop_controller.core import Files, Halt, sha, read_json
from loop_controller.continuous_tasks import TASKS
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.model import tool
from loop_controller.runner import git
from loop_controller.small_edits import SelectedEdit

SOURCE = 'b746be08fdb1e65c727ce6a876130d16a402482f'
ACCEPTED = 'd269dc43ac66c39afca4cb98ea53f9e7ed36806f'
FAILED = '109f8349ee6f9e6c580424fee65d7fd3e1dd8aec'
ROUND = 'q0049-292d36be'
BLOCKER = 'Halt: Repeated diagnosed blocker on chicago-polish-whole-route; failed source preserved and last playable state restored'
SCRIPT = 'Art/player.py'
SCRIPT_SHA = '76f5888887798186682a8fe9206b74dc640e997e5ac51456b93e6d0dae2d66de'


def validate_courier_pause(old):
    expected = dict(source_checkpoint=SOURCE, last_playable_checkpoint=ACCEPTED,
        current_round=ROUND, task_index=7, task_failures=7, failure_streak=1,
        diagnosis_used=True, overall_deadline_epoch=HARD_CAP_EPOCH, blocker=BLOCKER)
    if any(old.get(k) != v for k, v in expected.items()) or old.get('courier_art_continuation_attempted'):
        raise Halt('Expected the exact preserved q0049 camera rejection and accepted fallback')


class CourierArtResume(ThreeDayRunner):
    def validate_recovery(self, old):
        validate_courier_pause(old)
        if git(self.repo, 'diff', '--name-only', ACCEPTED, SOURCE, '--', 'game'):
            raise Halt('Courier continuation requires the exact accepted game tree')
        failed = read_json(self.store.root / ('evidence/' + ROUND + '/scoped-gate.json'))
        if failed.get('candidate_commit') != FAILED or failed.get('passed') is not False:
            raise Halt('Preserve the original failed camera gate')
        if sha((self.project / SCRIPT).read_bytes()) != SCRIPT_SHA:
            raise Halt('Original courier authoring source changed')

    def recovery_settings(self): return {'courier_art_continuation_attempted': True}

    def work(self):
        self.machine.guard()
        before, _, _ = accepted_fixture(self, self.store.get('latest_visual_milestone'))
        ident = 'q%04d-%s' % (self.store.get('rounds', 0) + 1, uuid.uuid4().hex[:8])
        self.store.set(current_round=ident, rounds=self.store.get('rounds', 0) + 1,
            stage='local-courier-art', current_task='One original courier hierarchy and silhouette improvement',
            task_design=NEXT_FOCUS)
        self.store.event('bounded-camera-followup-closed', failed_candidate=FAILED,
            restored_game_tree=ACCEPTED, outcome='unaccepted',
            reason='Vehicle branch has no enabling assignment; replacement replay misses combat/ending/failure.',
            original_failure_counts_preserved=True)
        files = Files(self.project, self.store); path = files.path(SCRIPT); raw = path.read_text()
        lines = raw.splitlines(keepends=True)
        first = next(i + 1 for i, line in enumerate(lines) if line.startswith('body = pivot('))
        last = next(i for i, line in enumerate(lines) if line.startswith('print('))
        edit = SelectedEdit(files, SCRIPT, first, last, max_lines=110)
        self.c.update(output_tokens=8192, model_timeout_seconds=400)
        self.store.report()
        self.model.session('builder', ident + '-courier-author',
            'You are the sole local Qwen original Blender author. Fix one measured visible courier asset problem.',
            'The camera follow-up is CLOSED as unaccepted. Work ONLY on this existing player asset; no camera, C#, '
            'mission, vehicle, collider or route edits. The accepted spawn image shows a malformed blocky courier. '
            'Native imported bounds show head center Y1.225, shoulders Y0.945, torso Y0.705, left upper arm Y1.695, '
            'left thigh Y1.105 and shoe center Y0.460 with height0.09 while pavement is Y0.14. Arms sit above the '
            'head and shoes do not meet the ground. The body pivot is offset; limb pivots are parented again to it '
            'using root-relative numbers, which must be reconciled as actual parent-local coordinates. '
            'Correct coherent hips/shoulders/limb placement and improve the recognizable human courier silhouette '
            '(head, shoulders, distinct legs/feet and clothing geometry) at chase distance. Preserve the documented '
            'feet origin, approximately1.8m height, forward/up basis, root identity and named animation pivots; '
            'do not delete or rename the animation interface. Keep meshes modest and original. '
            'Replace ONLY the supplied geometry/parenting span in one edit_selected_span call. Helper functions '
            'and materials outside it remain unchanged. At most110lines/6000bytes. A separate local export step '
            'follows; do not discuss a replay or call unavailable tools.\nFULL CURRENT SCRIPT:\n' + raw +
            '\nEXACT SPAN TO REPLACE:\n' + edit.old +
            '\nCURRENT ENGINE SETUP FOR COORDINATE CONTEXT (read only):\n' +
            files.path('Assets/Game/Bootstrap.cs').read_text().split('    public class Follow')[0],
            [tool('edit_selected_span', 'Save the corrected original courier geometry and parent-local placement.',
                  {'content': {'type': 'string'}})],
            {'edit_selected_span': lambda action, fields: edit.apply(action, fields['content'])},
            images=[('before.png ACTUAL accepted spawn t3.2', before / 'frame-000.png'),
                    ('Chicago target reference, not game output', self.refs / 'chicago_01_neighborhood_on_foot.png')],
            turns=1, reasoning_effort='low')
        if path.read_text() == raw: raise Halt('Courier author saved no change; no blind retry')
        ast.parse(path.read_text())
        candidate = self.checkpoint_source('Local Qwen: correct courier hierarchy and original silhouette')
        self.store.set(source_checkpoint=candidate, candidate_commit=candidate)
        export_saved_asset(self, SCRIPT, sha(path.read_bytes()), ident + '-export-only')
        candidate = self.checkpoint_source('Local Qwen: export corrected original courier asset')
        self.store.set(source_checkpoint=candidate, candidate_commit=candidate)
        if not qualify_saved_visual_candidate(self, TASKS[7], ident, candidate):
            raise Halt('Courier edit no longer qualifies for exact accepted visual replay')
        return ContinuousRunner.work(self)


if __name__ == '__main__': raise SystemExit(main(CourierArtResume))
