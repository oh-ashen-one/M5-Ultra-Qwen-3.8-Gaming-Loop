#!/usr/bin/env python3
"""Local Qwen fixes native-reproduced death handling across existing chapters."""
import json
from continue_game_queue import ReadBoundEdits
from resume_reticle_source import ReticleSource
from resume_camera_native_only import ACCEPTED
from resume_three_day_queue import main
from loop_controller.core import Files, Halt, atomic, read_json, sha
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.model import tool
from loop_controller.player_death_checks import CASES

NAMES = ('Bootstrap.cs','Combat.cs','Mission.cs','VehicleInteraction.cs','RouteMission.cs',
         'RelaySequence.cs','InterceptionMission.cs','MissionDirectorHud.cs')
ALLOWED = {'Assets/Game/' + name for name in NAMES}
TASK = dict(id='authoritative-player-death', phase='mission', visual_facing=False,
    outcome='Consistent death/failure authority across movement, firing, interactions, progression and reset')


class PlayerDeathSource(ReticleSource):
    def validate_recovery(self, old):
        expected = dict(status='paused', controller_pid=None, owned_process=None,
            last_playable_checkpoint=ACCEPTED, task_index=7, task_failures=24,
            failure_streak=1, diagnosis_used=True, overall_deadline_epoch=HARD_CAP_EPOCH,
            player_death_red_attempted=True,
            blocker='Halt: Chapter zero-health reproduction complete; local authoritative death-gating repair is next')
        self.red = old.get('player_death_red_outcome', {})
        if (any(old.get(k) != v for k, v in expected.items()) or old.get('player_death_source_attempted')
                or self.red.get('candidate') != old.get('source_checkpoint')
                or not self.red.get('all_setups_valid') or not self.red.get('all_cases_complete')
                or {x['case'] for x in self.red.get('cases', [])} != set(CASES)):
            raise Halt('Require complete native death reproduction on the current source and unchanged history')
        if not any(not x.get('passed') for x in self.red['cases']):
            raise Halt('Do not invent a game repair when all native death contracts pass')
        self.resume_capacity = self.priority_resume = self.transport_recovery = self.admission_recovery = False

    def recovery_settings(self):
        return dict(player_death_source_attempted=True, recovery_route='native-evidence-local-death-authority',
            recovery_change='Local Qwen receives exact current cross-component APIs and actual red observations; '
            'high reasoning, hash-backed edit tools and incremental source checkpoints. Native green and all '
            'healthy-route regressions follow with inference unloaded; no cloud gameplay substitution.')

    def work(self):
        ident = self.begin(TASK, 'local-authoritative-player-death')
        files = Files(self.project, self.store); edits = ReadBoundEdits(files)
        original = {path: files.path(path).read_text() for path in ALLOWED}
        follow = original['Assets/Game/Bootstrap.cs'].split('    public class Follow : MonoBehaviour')[1]
        new_paths = set()
        protected = {p: sha(p.read_bytes()) for p in self.project.rglob('*')
            if p.is_file() and p.suffix in ('.cs','.shader','.py','.fbx','.blend')
            and str(p.relative_to(self.project)) not in ALLOWED}
        context = []
        for name in NAMES:
            path = 'Assets/Game/' + name
            for start in range(1, len(original[path].splitlines())+1, 300):
                value = edits.read('context', dict(path=path, start_line=start, line_count=300))
                context.append(path + ' line' + str(start) + '\n' + value['content'])

        def validate(path, value):
            if path not in ALLOWED and path not in new_paths:
                raise ValueError('Edit only the supplied gameplay components or the one new original death authority')
            for forbidden in ('LoopRuntime','LoopPlayerDeathFixture','LoopInput.Replay','GetCommandLineArgs',
                              'Time.timeScale','Application.Quit','System.IO','LoopAimObservation'):
                if forbidden in value:
                    raise ValueError('No acceptance detection or external state manipulation: ' + forbidden)
            if path == 'Assets/Game/Bootstrap.cs':
                if value.split('    public class Follow : MonoBehaviour')[1] != follow:
                    raise ValueError('The qualified camera and reticle class must remain byte-for-byte intact')

        def checkpoint(result):
            self.store.set(source_checkpoint=self.checkpoint_source('Local Qwen: authoritative player death integration'))
            self.store.report()
            return result

        def replace(action, fields):
            current = files.path(fields['path']).read_text()
            if not fields['old'] or current.count(fields['old']) != 1:
                raise ValueError('Use one exact current source span')
            validate(fields['path'], current.replace(fields['old'], fields['new'], 1))
            return checkpoint(edits.replace(action, fields))

        def create(action, fields):
            path = fields['path']
            if (new_paths or path in ALLOWED or not path.startswith('Assets/Game/')
                    or not path.endswith('.cs') or path.count('/') != 2):
                raise ValueError('At most one new original Game C# component for shared death authority')
            new_paths.add(path)
            try:
                validate(path, fields['content'])
                return checkpoint(edits.create(action, fields))
            except Exception:
                if not files.path(path).exists(): new_paths.remove(path)
                raise

        def finish(_, fields):
            if all(files.path(path).read_text() == value for path,value in original.items()):
                raise ValueError('Integrate the measured death contract with existing systems before finishing')
            if any(sha(p.read_bytes()) != digest for p,digest in protected.items()):
                raise Halt('Local death author changed protected assets, camera shader or external source')
            return dict(ok=True, summary=fields['summary'], changed_files=[path for path,value in original.items()
                if files.path(path).read_text() != value] + sorted(new_paths), local_authored=True)

        evidence = [{k:row.get(k) for k in ('case','failure','injection_time','prior_chapter_state',
            'zero_health_samples','reset_samples','intervention')} for row in self.red['cases']]
        self.c.update(working_context_tokens=98304, output_tokens=16384, model_timeout_seconds=600)
        result = self.model.session('builder', ident + '-death-source',
            'You are local Qwen, sole gameplay author. Implement a coherent repair of the measured player-death integration defect.',
            'Native negative tests reached the existing chapters through ordinary input, injected health=0 once '
            'before game Update at recorded action boundaries, then attempted movement/fire/E/F and R reset. '
            'The attached results distinguish setup success from actual failures. This is an explicit negative '
            'fixture, not a claim that natural enemy damage was exercised in each chapter. Static review also '
            'found Combat only writes Mission failed when the old courier Mission is active; later route/relay '
            'systems lack death guards. Design one clear authoritative death/failure decision and integrate it '
            'consistently across foot/vehicle movement and boarding, player fire, courier/cache/relay/interception '
            'interactions and new progression, with an unmistakable visible health-depleted failure/reset message. '
            'Death must win when zero health and an objective action occur in the same frame. Later update order '
            'or completed legacy state must not resurrect input or authorize a new chapter. Preserve legitimate '
            'prior chapter receipts/history rather than faking a rewind. Already-ended chapters must not create '
            'new completion while the player is dead. Address receipt/arming windows as well as active combat. '
            'Use the actual health and reset APIs; do not forge completion, heal on death, suppress damage, disable '
            'the old rival to pass, widen shots, or add replay-dependent behavior. Ordinary R remains usable while '
            'dead and resets the player, vehicle, health, counters, failure state, every chapter and temporary '
            'targets so input-driven play resumes. Preserve all living-player movement parameters, timings, '
            'mission anchors, healthy progression, ray hit/occlusion behavior, art, camera and reticle. '
            'Material resource cleanup and typed countdown refactoring are separate queued findings; do not '
            'layer those unrelated rewrites into this critical fix. Missing-prefab reasons must not be made '
            'less truthful by a death message.\n'
            'You may edit only the supplied eight components and optionally create one original Game C# '
            'component for shared death authority. Choose its design; the controller does not prescribe class '
            'architecture. Bootstrap/Walker integration is allowed but its entire Follow class is protected. '
            'Keep existing public chapter APIs for passive observation. Tool context below contains exact '
            'current source and records its hashes, so an initial replace_text can use a supplied exact span. '
            'After an edit, read_file refreshes the current hash before further edits to that file. Save complete '
            'logical changes through tools promptly; each save is checkpointed with local authorship. '
            'Use xhigh reasoning for cross-component ordering and reset correctness.16,384output tokens per '
            'response and bounded tool turns are available. Return finish_task after complete integration, '
            'not a prose-only design. No native engine runs during this author phase; green tests follow.\n'
            'READ-ONLY API: LoopSignals.Health is float; Restarts,Shots,Hits,PursuitLevel are int; Mode/Mission '
            'are string; Player/Vehicle are Transform. LoopInput.Pressed(KeyCode), Held(KeyCode), MoveX/MoveY '
            'are ordinary input adapters. Do not modify these external interfaces.\n'
            'ACTUAL NATIVE RED FINDINGS:\n' + json.dumps(evidence) + '\nEXACT CURRENT SOURCE:\n' + '\n\n'.join(context),
            [tool('read_file','Read current exact source/hash before a later edit.',
                  {'path':{'type':'string'},'start_line':{'type':'integer'},'line_count':{'type':'integer'}},['path']),
             tool('replace_text','Replace one exact read-backed source span.',
                  {'path':{'type':'string'},'old':{'type':'string'},'new':{'type':'string'}}),
             tool('create_file','Create one original shared death-state component.',
                  {'path':{'type':'string'},'content':{'type':'string'}}),
             tool('finish_task','Finish the complete saved integration; native verification follows.',{'summary':{'type':'string'}})],
            {'read_file':edits.read,'replace_text':replace,'create_file':create,'finish_task':finish},
            turns=12, reasoning_effort='xhigh')
        atomic(self.store.root / 'evidence' / (ident + '-death-author.json'), result)
        if not result.get('ok'):
            raise Halt('Local death integration incomplete; preserve all saved source and bounded response for changed continuation')
        self.store.set(stage='player-death-source-saved-awaiting-native',
            player_death_source_outcome=dict(candidate=self.store.get('source_checkpoint'), round=ident,
                local_authored=True, native_verified=False, changed_files=result['changed_files'], final_game_accepted=False))
        self.store.report()
        raise Halt('Local death integration saved; unload the idle model for native green and healthy-route regressions')


if __name__ == '__main__':
    raise SystemExit(main(PlayerDeathSource))
