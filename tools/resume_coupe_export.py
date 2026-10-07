#!/usr/bin/env python3
"""Complete q0048's omitted export without reauthoring its local-Qwen asset."""
from continue_game_queue import ContinuousRunner
from resume_three_day_queue import ThreeDayRunner, main
from qualify_visual_replay import qualify_saved_visual_candidate, validate_exports
from loop_controller.core import Halt, sha
from loop_controller.continuous_tasks import TASKS
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.model import tool
from loop_controller.runner import git

SOURCE = '5c8117228d1fb5a3ad1dea881192c9905ac3d40c'
ACCEPTED = 'e38b0681046fb39cab7f8ec182495903729b5ae6'
ROUND = 'q0048-8e962e4d'
SCRIPT = 'Art/coupe.py'
SCRIPT_SHA = '9630f574cc8107be2e986e6f5718fe1c92b72f552841b7932e27f1ef0ff408f6'
BLOCKER = 'Halt: Visual authoring script changed after its export'


def validate_coupe_export_pause(old):
    expected = dict(source_checkpoint=SOURCE, last_playable_checkpoint=ACCEPTED,
        current_round=ROUND, task_index=7, task_failures=6, failure_streak=1,
        diagnosis_used=True, overall_deadline_epoch=HARD_CAP_EPOCH, blocker=BLOCKER)
    if any(old.get(k) != v for k, v in expected.items()) or old.get('coupe_export_completion_attempted'):
        raise Halt('Expected only the untouched q0048 omitted-export stop; preserve other faults')


def export_saved_coupe(runner):
    return export_saved_asset(runner, SCRIPT, SCRIPT_SHA, ROUND + '-export-only')


def export_saved_asset(runner, script_path, script_sha, session_id):
    """Offer the local model one export, with no source-edit or engine-retry tools."""
    if script_path not in {'Art/' + n + '.py' for n in ('street', 'coupe', 'props', 'player')}:
        raise Halt('Export completion is limited to the four existing original assets')
    script = runner.project / script_path
    if sha(script.read_bytes()) != script_sha:
        raise Halt('Saved local asset source changed before export')
    attempted = []
    def export(action, _):
        if attempted: raise Halt('One export attempt only; preserve failures for diagnosis')
        attempted.append(action)
        if sha(script.read_bytes()) != script_sha:
            raise Halt('Saved local asset source changed during export completion')
        result = runner.engines.blender(runner.project, script_path, action)
        if not result.get('ok'): raise Halt('Saved asset export failed; no automatic retry')
        validate_exports(runner.project, [script.stem])
        return result
    def finish(_, fields):
        if not attempted: raise ValueError('Run the offered Blender export before finishing')
        validate_exports(runner.project, [script.stem])
        return {'ok': True, 'summary': fields['summary'][:1000]}
    runner.c.update(output_tokens=4096, model_timeout_seconds=240)
    runner.store.set(stage='local-saved-' + script.stem + '-export'); runner.store.report()
    runner.model.session('builder', session_id,
        'You are local Qwen completing the export of your saved original asset.',
        'Your saved ' + script_path + ' needs a matching export. Call run_blender once, then finish_task. '
        'Do not redesign or rewrite anything. Your exact saved script is:\n' + script.read_text(),
        [tool('run_blender', 'Export the exact saved asset through the protected adapter.', {}),
         tool('finish_task', 'Finish after the verified export.', {'summary': {'type': 'string'}})],
        {'run_blender': export, 'finish_task': finish}, turns=2, reasoning_effort='low')
    if not attempted or sha(script.read_bytes()) != script_sha:
        raise Halt('Saved asset export incomplete or source changed; preserve work')
    validate_exports(runner.project, [script.stem])


class CoupeExportResume(ThreeDayRunner):
    def validate_recovery(self, old):
        validate_coupe_export_pause(old)
        if git(self.repo, 'diff', '--name-only', ACCEPTED, SOURCE).splitlines() != ['game/' + SCRIPT]:
            raise Halt('Expected only the saved coupe authoring change')
        if self.store.db.execute("SELECT 1 FROM actions WHERE kind='blender' AND id LIKE ?",
                                 (ROUND + '%',)).fetchone():
            raise Halt('A previous coupe export action exists; reconcile it before any retry')

    def recovery_settings(self): return {'coupe_export_completion_attempted': True}

    def work(self):
        self.machine.guard()
        export_saved_coupe(self)
        candidate = self.checkpoint_source('Local Qwen: export saved q0048 coupe geometry')
        self.store.set(source_checkpoint=candidate, candidate_commit=candidate)
        self.store.event('saved-coupe-export-completed', original_candidate=SOURCE,
            candidate=candidate, source_unchanged=True, original_failure_counts_preserved=True)
        if not qualify_saved_visual_candidate(self, TASKS[7], ROUND, candidate):
            raise Halt('Exported coupe no longer qualifies for protected visual replay')
        return ContinuousRunner.work(self)


if __name__ == '__main__': raise SystemExit(main(CoupeExportResume))
