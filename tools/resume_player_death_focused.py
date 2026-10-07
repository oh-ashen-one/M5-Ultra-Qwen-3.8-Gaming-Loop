#!/usr/bin/env python3
"""Resume the preserved partial death repair with separate bounded source contexts."""
import json
import re

from continue_game_queue import ReadBoundEdits
from resume_player_death_source import PlayerDeathSource, NAMES, TASK
from resume_camera_native_only import ACCEPTED
from resume_three_day_queue import main
from loop_controller.core import Files, Halt, atomic, read_json, sha
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.model import tool

PARTIAL = 'b0254e416bc6592aac103d4a9885ae2fcb9d5b83'
AUTHORITY = 'Assets/Game/DeathAuthority.cs'
BOOT = 'Assets/Game/Bootstrap.cs'
FOLLOW = '    public class Follow : MonoBehaviour'
PHASES = (
    ('authority', ('DeathAuthority.cs',),
     'Correct the saved but uninstalled DeathAuthority. Keep one authoritative live-health death decision '
     'and latch until the real Restarts counter changes. Remove the positive-health grace that releases '
     'death without R. Use the supplied concrete LoopSignals fields directly; no reflection or tolerant '
     'fake defaults. Keep the component compact (at most160lines), retaining a public IsDead decision '
     'and Install(GameObject,Camera) entry point for the following integration. The existing MissionBoard '
     'will render failure in the final phase; do not build another banner or allocate presentation assets. '
     'Never write health, reset counters, objective completion, input or camera state from this authority. '
     'Handle same-frame zero health and ordinary reset ordering. Save the complete corrected component.'),
    ('controls', ('Bootstrap.cs','VehicleInteraction.cs','Combat.cs','Mission.cs'),
     'Install the supplied corrected DeathAuthority once from Bootstrap. Integrate its actual IsDead API '
     'across Walker movement, vehicle steering/throttle/boarding/exiting, player firing and legacy courier '
     'pickup/delivery. Preserve ordinary R while dead and all reset consumers. Process reset edges before '
     'dead-input exits; prevent residual commanded vehicle velocity from moving the dead player. Natural '
     'rival damage remains real, and lethal damage in the current update must prevent the following player '
     'shot. Preserve ray hit/occlusion behavior, input bindings, healthy motion parameters, mission timing '
     'and already earned completion. Do not modify the entire protected Follow camera/reticle class. '
     'Do not edit the authority or later chapters in this phase.'),
    ('chapters', ('RouteMission.cs','RelaySequence.cs','InterceptionMission.cs','MissionDirectorHud.cs'),
     'Integrate the supplied DeathAuthority across route activation/interaction, relay arming/final '
     'interaction, interception arming/receipt/spawn/completion and its physics/late-update paths. Death '
     'wins simultaneous objective input; a previously completed chapter cannot start a new chapter while '
     'dead. Preserve genuine prior receipts/counters instead of rewinding history. Ordinary R resets '
     'every chapter and temporary runner. Give the existing MissionBoard unmistakable health-depleted '
     'failure and R-reset text with priority over live or completed chapter text. Preserve any more '
     'specific pre-existing failure reason. Do not rewrite countdown parsing, material cleanup, art or '
     'other unrelated findings. Keep current public chapter observation APIs and healthy timings intact.'),
)


def validate_boundary(old):
    expected = dict(status='paused', controller_pid=None, owned_process=None,
        source_checkpoint=PARTIAL, current_round='q0143-c432e36d', last_playable_checkpoint=ACCEPTED,
        task_index=7, task_failures=24, failure_streak=1, diagnosis_used=True,
        overall_deadline_epoch=HARD_CAP_EPOCH, player_death_source_attempted=True,
        blocker='URLError: <urlopen error [Errno 61] Connection refused>')
    fault = old.get('player_death_source_fault', {})
    if (any(old.get(k) != v for k,v in expected.items()) or old.get('player_death_focused_attempted')
            or fault.get('candidate') != PARTIAL or fault.get('complete_integration') is not False
            or fault.get('cause') != 'resident available-memory guard'
            or not old.get('player_death_red_outcome', {}).get('all_setups_valid')):
        raise Halt('Require the diagnosed resource stop and exact preserved partial local source')


def validate_edit(path, value, writable, follow):
    if path not in writable:
        raise ValueError('Edit only the current phase files; the supplied other APIs are read-only')
    if any(s in value for s in ('LoopRuntime','LoopPlayerDeathFixture','LoopInput.Replay',
            'GetCommandLineArgs','Time.timeScale','Application.Quit','System.IO','LoopAimObservation')):
        raise ValueError('No acceptance detection, external state or runtime manipulation')
    if path == BOOT and (value.count(FOLLOW) != 1 or value.split(FOLLOW)[1] != follow):
        raise ValueError('Keep the qualified complete Follow class byte-for-byte intact')
    if path == AUTHORITY and ('System.Reflection' in value or len(value.splitlines()) > 160
            or re.findall(r'\bclass\s+(\w+)', value) != ['DeathAuthority']):
        raise ValueError('One compact DeathAuthority class, at most160lines, with concrete signal APIs')


class FocusedDeath(PlayerDeathSource):
    phases=PHASES
    phase_turns=10
    allow_unchanged_phases=()
    def validate_recovery(self, old):
        validate_boundary(old)
        self.red = old['player_death_red_outcome']
        self.resume_capacity = self.priority_resume = self.transport_recovery = self.admission_recovery = False

    def recovery_settings(self):
        return dict(player_death_focused_attempted=True,
            recovery_route='resource-diagnosed-fresh-small-integration-contexts',
            recovery_change='Preserve partial source and fault; local xhigh author uses three fresh scoped '
            'contexts instead of replaying growing private history. Resource, ownership and native gates unchanged.')

    def wait_for_capacity(self):
        self.capacity.wait('local-death-focused-integration')

    def work(self):
        ident = self.begin(TASK, 'local-death-focused-integration')
        files = Files(self.project, self.store)
        baseline = {str(p.relative_to(self.project)): sha(p.read_bytes()) for p in self.project.rglob('*')
            if p.is_file() and p.suffix in ('.cs','.shader','.py','.fbx','.blend')}
        follow = files.path(BOOT).read_text().split(FOLLOW)[1]
        all_writable = {AUTHORITY} | {'Assets/Game/'+n for n in NAMES}
        results = []
        for label, names, instruction in self.phases:
            writable = {'Assets/Game/'+n for n in names}
            readable = writable | {AUTHORITY}
            original = {p: files.path(p).read_text() for p in writable}
            phase_protected = {p: sha(files.path(p).read_bytes()) for p in baseline if p not in writable}
            edits = ReadBoundEdits(files)
            context = []
            def read(action, fields):
                if fields['path'] not in readable:
                    raise ValueError('Only supplied current-phase files and DeathAuthority are readable; '
                                     'the concrete LoopSignals/LoopInput API is provided in the brief')
                return edits.read(action, fields)
            for path in sorted(readable):
                source = files.path(path).read_text()
                last = source[:source.index(FOLLOW)].count('\n') if path == BOOT else len(source.splitlines())
                for start in range(1, last+1, 300):
                    value = read('context', dict(path=path, start_line=start, line_count=min(300,last-start+1)))
                    context.append(path+' line'+str(start)+'\n'+value['content'])
            def replace(action, fields):
                path = fields['path']; current = files.path(path).read_text()
                if not fields['old'] or current.count(fields['old']) != 1:
                    raise ValueError('Use one exact current source span')
                validate_edit(path, current.replace(fields['old'], fields['new'],1), writable, follow)
                result = edits.replace(action, fields)
                self.store.set(source_checkpoint=self.checkpoint_source('Local Qwen: death integration '+label))
                self.store.report()
                return result
            def finish(_, fields):
                if (all(files.path(p).read_text() == value for p,value in original.items())
                        and label not in self.allow_unchanged_phases):
                    raise ValueError('Save the actual current-phase integration before finishing')
                if any(sha(files.path(p).read_bytes()) != digest for p,digest in phase_protected.items()):
                    raise Halt('Focused local author changed protected other-phase source')
                return dict(ok=True, summary=fields['summary'], phase=label, local_authored=True,
                    changed_files=[p for p,v in original.items() if files.path(p).read_text() != v])
            self.c.update(working_context_tokens=49152, output_tokens=16384, model_timeout_seconds=600)
            self.store.set(stage='local-death-'+label);self.store.report()
            result = self.model.session('builder',ident+'-death-'+label,
                'You are local Qwen, sole game-code author. Save complete scoped integration edits through tools.',
                instruction+'\nThe prior resource stop and partial source remain preserved. This is a fresh '
                'smaller context, not a replay of that long private conversation. Native tests already reproduce '
                'movement/fire after zero health at six chapter boundaries. Four also advance objectives. '
                'The identical negatives, ordinary95-second route and all ten regressions follow complete '
                'integration. Do not target or modify acceptance. Use xhigh reasoning and save logical changes '
                'promptly; finish_task only after this phase is complete. Each edit is a local source checkpoint. '
                'read_file accepts1..300lines; after editing a file, refresh its current hash before another edit. '
                'All initial spans below are exact and already read/hash-backed. No installs, new files, assets, '
                'engine runs or unrelated refactors.\nCONCRETE READ-ONLY API: LoopSignals.Health is float; '
                'Restarts,Shots,Hits,PursuitLevel are int; Mode,Mission are string; Player,Vehicle are Transform. '
                'LoopInput.Pressed(KeyCode),Held(KeyCode),MoveX,MoveY are ordinary input adapters. '
                'Do not search for or rewrite external signal/input files.\nCURRENT SOURCE:\n'+'\n\n'.join(context),
                [tool('read_file','Read exact current source and hash;1..300lines.',
                    {'path':{'type':'string'},'start_line':{'type':'integer','minimum':1},
                     'line_count':{'type':'integer','minimum':1,'maximum':300}},['path']),
                 tool('replace_text','Replace one exact current read-backed span.',
                    {'path':{'type':'string'},'old':{'type':'string'},'new':{'type':'string'}}),
                 tool('finish_task','Finish the saved current phase; native verification is separate.',
                    {'summary':{'type':'string'}})],
                {'read_file':read,'replace_text':replace,'finish_task':finish},turns=self.phase_turns,reasoning_effort='xhigh')
            atomic(self.store.root/'evidence'/(ident+'-death-'+label+'.json'),result)
            if not result.get('ok'):
                raise Halt('Focused death '+label+' incomplete; preserve source and diagnose changed continuation')
            results.append(dict(**result,candidate=self.store.get('source_checkpoint')))
            self.store.set(player_death_focused_phases=results);self.store.report()
        if any(sha(files.path(p).read_bytes()) != h for p,h in baseline.items() if p not in all_writable):
            raise Halt('Focused integration changed protected source')
        changed = [p for p,h in baseline.items() if sha(files.path(p).read_bytes()) != h]
        result = dict(ok=True,local_authored=True,changed_files=changed,phases=results)
        self.finish_author(ident,result)

    def finish_author(self,ident,result):
        atomic(self.store.root/'evidence'/(ident+'-death-author.json'),result)
        self.store.set(stage='player-death-source-saved-awaiting-native',player_death_source_outcome=dict(
            candidate=self.store.get('source_checkpoint'),round=ident,local_authored=True,
            native_verified=False,changed_files=result['changed_files'],final_game_accepted=False))
        self.store.report()
        raise Halt('Local death integration saved; unload the idle model for native green and healthy-route regressions')


if __name__ == '__main__':
    raise SystemExit(main(FocusedDeath))
