#!/usr/bin/env python3
"""Local Qwen authors the planned moving encounter; capture its first native evidence."""
import json
import re
from resume_combat_death import CombatDeath, SOURCE, ACCEPTED
from resume_hud_presentation_polish import compact
from resume_three_day_queue import main
from continue_game_queue import ReadBoundEdits
from loop_controller.core import Files, Halt, atomic, read_json, sha
from loop_controller.model import tool
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.continuous_checks import validate_proposed

ROUND = 'q0123-bc8e98e4'
PATH = 'Assets/Game/InterceptionMission.cs'
BOOT = 'Assets/Game/Bootstrap.cs'
HUD = 'Assets/Game/MissionDirectorHud.cs'
TASK = dict(id='moving-target-encounter', phase='mission', checks=[], maximum=100, coverage='mission-core',
    outcome='Stop three actual moving rivals after the relay, with collision, real shots, failure and whole reset')


def validate_pause(old):
    expected=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=ROUND,
        task_index=7,task_failures=24,failure_streak=1,diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,
        stage='native-combat-lethal-reset',
        blocker='Halt: Actual lethal-hit/reset qualified; continue local moving-target encounter implementation')
    result=old.get('combat_death_outcome',{})
    if (any(old.get(k)!=v for k,v in expected.items()) or old.get('moving_encounter_attempted')
        or result.get('candidate')!=SOURCE or not result.get('passed')):
        raise Halt('Require exact actual lethal-hit/reset qualification and unchanged history')


def validate_source(content):
    if not isinstance(content,str) or not 30<=len(content.splitlines())<=240 or len(content.encode())>16000:
        raise ValueError('One complete bounded component,30..240lines and at most16KB')
    for word in ['LoopRuntime','LoopInterceptionObservation','LoopCombatObservation','LoopInput.Replay',
                 'GetCommandLineArgs','System.IO','System.Reflection','CreatePrimitive','SetValue','Time.timeScale',
                 'Random.InitState','Application.Quit','Input.Get','HandleFire','KeyCode.Mouse0']:
        if word in content: raise ValueError('Forbidden game ownership or replay coupling: '+word)
    if re.search(r'LoopSignals\.\w+\s*(?:\+\+|--|[+\-*/]?=(?!=))',content):
        raise ValueError('Read existing signals only; do not forge earlier mission/combat outcomes')
    for word in ['class InterceptionMission','RivalAgent','Rigidbody','FixedUpdate','SweepTest','LoopSignals.Restarts',
                 'Active','Complete','Failed','Stopped','Escaped','Spawned','Objective','Install']:
        if word not in content: raise ValueError('Required actual moving encounter API missing: '+word)
    return content


def exploratory_probe(original):
    steps=[s for s in original['steps'] if s['end']<=60]
    steps += [dict(start=60.3,end=73.3,keys=['D']),dict(start=73.6,end=73.9,keys=['A']),
              dict(start=90,end=90.3,keys=['R']),dict(start=92,end=93,keys=['W'])]
    return validate_proposed(dict(duration=95,steps=steps,captures=[3.2,59.75,64.5,74.5,84.5,90.6,94]),100,'mission-core')


class MovingEncounter(CombatDeath):
    def validate_recovery(self,old):
        validate_pause(old)
        self.resume_capacity=False; self.priority_resume=False; self.transport_recovery=False
        self.admission_recovery=False
        e=self.store.root / old['combat_death_outcome']['evidence']
        gate=read_json(e/'combat-death-gate.json')
        if not gate.get('passed') or not gate.get('death_reset',{}).get('passed') or gate.get('candidate_commit')!=SOURCE:
            raise Halt('Require actual native lethal-hit/reset proof')

    def wait_for_capacity(self): self.capacity.wait('local-moving-encounter-source')

    def recovery_settings(self):
        return dict(moving_encounter_attempted=True,recovery_route='local-moving-target-encounter',
            recovery_change='Local Qwen adds a separately observed moving-target stage in the existing east street. '
            'Existing Combat alone owns fire/damage. Native exploration is not positive gameplay qualification. '
            'Original health pressure, real collision/escape, secondary-target isolation and reset remain required.')

    def source(self,ident):
        actual='\n\n'.join(name+'\n'+(self.project/'Assets/Game'/name).read_text()
            for name in ['RelaySequence.cs','Combat.cs','MissionDirectorHud.cs'])
        files=Files(self.project,self.store); edits=ReadBoundEdits(files)
        before={p:sha(p.read_bytes()) for p in self.project.rglob('*.cs')}
        self.c.update(output_tokens=8192,model_timeout_seconds=360)
        result=self.model.session('builder',ident+'-source',
            'You are local Qwen, sole substantive game author. Implement the bounded planned encounter.',
            'Create ONE complete ChicagoGame.InterceptionMission MonoBehaviour source file. No markdown. '
            'Public static Install(GameObject player, Camera cam) makes one named InterceptionMission host; '
            'DefaultExecutionOrder(100) runs after existing reset/relay updates. Public fields bool Active,Complete,Failed; '
            'int Stopped,Escaped,Spawned; string Objective; these represent actual gameplay. '
            'Read the existing RelaySequence and arm only on its real AllComplete, after a3second readable receipt '
            '(this delay is NOT mission content). The existing route ends59.63s at player(28.62,.195,25.95), '
            'health44, original live rival(22.15,.14,17.03). If player stands still the original rival kills them '
            'by78s. Preserve that rival and existing health; failure at Health<=0 must be truthful. Never heal, '
            'teleport, disable the old threat, invent legacy completion or write any LoopSignals. '
            'Planned new action: stop3runners before any escapes. Spawn3 ORIGINAL player-mesh clones at '
            '(24,.2,22),(24,.2,18),(24,.2,14), stagger0/6/12seconds after arming. Reuse '
            'Resources.Load<GameObject>("Generated/player/scene") with the known localY -0.79 import correction '
            'as in Combat.Build; no primitive fallback or downloaded asset. Missing prefab is a visible failure. '
            'Root names InterceptRunner1/2/3, root scaleone, one CapsuleCollider(center0,.95,0;height1.9;radius.38), '
            'one dynamic gravity Rigidbody mass80, FreezeRotation, continuous collision detection, distinct '
            'muted hostile material from existing Standard shader. Remove imported child colliders/rigidbodies. '
            'Attach the EXISTING RivalAgent, hp3/alive=true. Do not implement fire or another Mouse0 reader. '
            'Existing Combat.HandleFire alone decrements the actual nearest-hit RivalAgent and disables that '
            'struck agent renderer/capsule on real hp0; that receiver fix and original death/reset were verified. '
            'Move each live unresolved runner +X1.6m/s toward escapeX58 in FixedUpdate using dynamic body '
            'horizontal velocity, preserving vertical gravity. Use Rigidbody.SweepTestAll (filter own body '
            'and floor upward normals) to stop horizontal velocity before real blocking geometry. NEVER '
            'transform-position += or MovePosition a dynamic body through walls. Ground is actual '
            'X22..60/Z8..28; pavementtop.14, sidewalkstop.20, physical barriers atX60.25 andZ7.75/28.25. '
            'Do not create new world/geometry or move anchors. Visible body must stay grounded in real collision. '
            'Count a stop ONCE only when actual agent hp<=0 and !alive; freeze that defeated body so its '
            'disabled capsule does not fall forever. Distinct per-runner resolved/escaped tracking must prevent '
            'double counts. A living runner reachingX58 is escaped, NOT a kill: increment Escaped once, '
            'disable its visible renderers/collider, freeze body, keep its hp/alive unchanged and latch Failed. '
            'Complete iff all3 actual distinct stops, no escapes and health>0. Latch failure/ending; freeze '
            'other bodies after either. On any LoopSignals.Restarts change destroy all new targets, clear '
            'counts/flags/timing, return inactive and wait for a NEW relay completion; do not immediately '
            'rearm from stale prior state. No changes to prior courier/route/relay, existing combat/camera/input. '
            'Provide Objective with <=4lines, each<=40characters: actual INTERCEPT RUNNERS n/3, '
            'Move to aim; Mouse0 fire, real stopped/escaped counts, Relay complete | R reset. Completion and '
            'failure must be explicit with R reset and truthful counts. No new HUD card; MissionDirectorHud '
            'will read this field at higher priority only while Active, preserving separate health/wanted. '
            'Target concise robust source<200lines. Save via create_encounter now.\nEXACT EXISTING APIs:\n'+actual,
            [tool('create_encounter','Save the complete bounded new moving-encounter component.',{'content':{'type':'string'}})],
            {'create_encounter':lambda a,f:edits.create(a,dict(path=PATH,content=validate_source(f['content'])))},
            turns=2,reasoning_effort='low')
        if not (self.project/PATH).exists(): raise Halt('Local moving encounter was not saved: '+json.dumps(result))
        if any(sha(p.read_bytes())!=digest for p,digest in before.items()): raise Halt('Creation changed prior game source')
        candidate=self.checkpoint_source('Local Qwen: moving interception mission')
        self.store.set(source_checkpoint=candidate,candidate_commit=candidate)
        raw=(self.project/BOOT).read_text(); old=next(s for s in raw.splitlines(True) if 'RelaySequence.Install(body,cam);' in s)
        expected=old+'InterceptionMission.Install(body,cam);\n'
        self.patch(ident,'install-moving-encounter',BOOT,old,
            'Preserve the selected relay install; append InterceptionMission.Install(body,cam); exactly once.',
            lambda value,_:compact(value)==compact(expected),3)
        raw=(self.project/HUD).read_text(); old=next(s for s in raw.splitlines(True) if 'RelaySequence _relay;' in s)
        expected=old+'InterceptionMission _interception;\n'
        self.patch(ident,'moving-encounter-hud-reference',HUD,old,
            'Preserve this field declaration; append InterceptionMission _interception; only.',
            lambda value,_:compact(value)==compact(expected),3)
        raw=(self.project/HUD).read_text(); old='            string s = null;\n            if (_relay != null && _relay.Active)'
        expected='if (!_interception) _interception = FindAny<InterceptionMission>();\nstring s = null;\nif (_interception != null && _interception.Active) s = _interception.Objective;\nelse if (_relay != null && _relay.Active)'
        self.patch(ident,'moving-encounter-current-objective',HUD,old,
            'At this selected objective branch, reacquire missing InterceptionMission via FindAny<InterceptionMission>(); '
            'keep string s=null; then priority if(_interception!=null && _interception.Active) s=_interception.Objective; '
            'else if existing relay condition. Preserve the following relay branch/body and every old mechanic/panel.',
            lambda value,_:compact(value)==compact(expected),6)
        return self.store.get('source_checkpoint')

    def work(self):
        ident=self.begin(TASK,'local-moving-encounter-source'); candidate=self.source(ident)
        original=read_json(self.store.root/'evidence/q0120-dc4867c8-positive/captures/scenario.json')
        probe=exploratory_probe(original)
        self.store.set(stage='native-moving-encounter-exploration'); self.store.report()
        bundle=self.store.root/'evidence'/(ident+'-exploration')
        gate=self.engines.unity(self.project,bundle,probe,candidate)
        result=dict(candidate=candidate,evidence=str(bundle.relative_to(self.store.root)),native=gate,
            gameplay_qualified=False,secondary_target_isolation_qualified=False,final_game_accepted=False)
        atomic(bundle/'moving-encounter-exploration.json',result)
        self.store.set(moving_encounter_exploration=result); self.store.report()
        if not gate.get('passed'): raise Halt('Moving encounter first native evidence requires measured diagnosis')
        raise Halt('Moving encounter source and first native exploration saved; qualify actual moving hits, isolation, escape and whole reset')


if __name__ == '__main__': raise SystemExit(main(MovingEncounter))
