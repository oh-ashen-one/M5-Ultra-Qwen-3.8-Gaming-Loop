#!/usr/bin/env python3
"""Qualify a saved door-only edit, then author a genuinely new connected street."""
import json
import uuid
from continue_game_queue import ContinuousRunner, ReadBoundEdits, failure_key
from resume_three_day_queue import ThreeDayRunner, main
from resume_alley_presentation import REPLAY
from qualify_map_extension import MAP_TASK, qualify_extension_native, promote_qualified_extension
from loop_controller.core import Files, Halt, atomic, sha, verify_seal
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.model import tool
from loop_controller.prop_clone_checks import inspect_alley_clones, inspect_door_layers
from loop_controller.recovery_policy import replay_identity
from loop_controller.replay_contract import finish_tool, validate_submission
from loop_controller.runner import git

SOURCE='bc4f350e57e0b0632aeef5d3498ec30a66ad2bf2'
ACCEPTED='c9bbf1acc28a26c2a0d06a83da4d3b2b44cde188'
ROUND='q0077-c5f06ea7'
RESPONSE_SHA='59445dd2628b42076577e06a21da019f8e705b6f2ac3fb41dd09eb3653d7e714'
PATH='Assets/Game/WorldColliders.cs'
STREET_PATHS=(PATH,'Assets/Game/ConnectedStreet.cs')
BLOCKER='Halt: Replay-only role supplied no valid finish_task; required: summary, duration, input_steps, captures'
DOOR_TASK={**MAP_TASK,'outcome':'The saved wood door is visible ahead of its stone backing; preserve the accepted connector and every regression.',
    'instructions':'Qualify only the saved0.07m wood-panel depth correction with unchanged accepted inputs. '
    'Require actual visible dark wood ahead of the pale stone backing in the north-wall door atX16. '
    'Keep the accepted rough connector scope; unrelated existing polish remains future work. '
    'This does not establish a second street, larger area or ten-minute mission.'}
SECOND_TASK={**MAP_TASK,'prior_bounds':[[-1,6,-2,30],[6,22,8,20]],
    'outcome':'A second connected street beyond the already accepted core and alley, walked and driven out and back.',
    'instructions':'Create one connected street continuing east from the current alley end atX22. '
    'A useful provisional footprint isX22..60,Z8..28; the local author owns the final implementation. '
    'Reuse existing original pavement, facade and fence meshes with visible support and matching collisions. '
    'Replace only the east alley boundary that becomes an interior junction; close every new outer edge. '
    'Preserve the old core, south/north alley walls, service door, lights, props, camera, mission anchors and controls. '
    'Preserve complete source world transforms, mesh/material assignments and child colliders. '
    'Keep ground topY0.14. No new art volume or primitives. Some original windows may be reused later; '
    'do not mix facade work or mission pacing into this topology change. '
    'The acceptance boundary is now the UNION ofX-1..6,Z-2..30 andX6..22,Z8..20. '
    'Prove actual foot and vehicle travel at least6m beyond BOTH old rectangles, then physical return to either, '
    'with visible captures of each outside leg and its return, no R reset, within150seconds. '
    'A repeat of the first alley replay cannot pass. This is a foundation topology milestone, not final art or pacing.'}


def validate_pause(old):
    expected=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=ROUND,
        task_index=7,task_failures=19,failure_streak=2,diagnosis_used=True,
        overall_deadline_epoch=HARD_CAP_EPOCH,blocker=BLOCKER)
    if any(old.get(k)!=v for k,v in expected.items()) or old.get('saved_door_recovery_attempted'):
        raise Halt('Expected exact preserved door-only replay stop')


def door_only(before,after):
    def code(raw):return '\n'.join(line for line in raw.splitlines() if not line.strip().startswith('//'))
    old='dgo.transform.position += new Vector3(16f - db.center.x, 0.14f - db.min.y, 19.92f - db.center.z);'
    new=old.replace('19.92f','19.85f')
    # The first of two equal original lines is the wood panel, the second the stone.
    return code(after)==code(before).replace(old,new,1) and code(after)!=code(before)


class SavedDoor(ThreeDayRunner):
    def validate_recovery(self,old):
        validate_pause(old)
        if git(self.repo,'diff','--name-only',ACCEPTED,SOURCE,'--','game')!='game/'+PATH:
            raise Halt('Recovery is restricted to one measured door edit')
        if not door_only(git(self.repo,'show',ACCEPTED+':game/'+PATH),(self.project/PATH).read_text()):
            raise Halt('Saved source is not the original measured door correction')
        raw=(self.store.root/'private/sessions'/ (ROUND+'-replay')/'response-000.json').read_bytes()
        if sha(raw)!=RESPONSE_SHA:raise Halt('Preserve original exhausted replay response')
        choice=json.loads(raw)['choices'][0]
        if choice.get('finish_reason')!='length' or choice['message'].get('tool_calls'):
            raise Halt('Expected preserved output exhaustion with no executable submission')
        self.accepted_probe()

    def accepted_probe(self):
        record=self.store.get('accepted_map_extension');bundle=self.store.root/record['evidence']
        note='game/Notes/map-'+bundle.name+'.json'
        if json.loads(git(self.repo,'show',ACCEPTED+':'+note))!=record:
            raise Halt('Accepted map receipt differs from its preserved Git note')
        manifest=verify_seal(bundle/'captures',record['capture_manifest_sha256'])
        if manifest.get('candidate')!=record['candidate']:raise Halt('Accepted map source/evidence mismatch')
        probe=json.loads((bundle/'captures/scenario.json').read_text())
        if replay_identity(probe)!=REPLAY:raise Halt('Preserve accepted connector physical inputs')
        return probe

    def recovery_settings(self):
        return dict(saved_door_recovery_attempted=True,recovery_route='saved-door-then-second-street',
            recovery_change='Reuse accepted replay for the saved presentation edit, then separate small topology scope',
            second_street_attempts=0)

    def begin(self,task,stage):
        self.machine.guard()
        ident='q%04d-%s'%(self.store.get('rounds',0)+1,uuid.uuid4().hex[:8])
        self.store.set(current_round=ident,rounds=self.store.get('rounds',0)+1,phase=task['phase'],
            current_task=task['outcome'],stage=stage,next_task='Connected street, facade assemblies, then meaningful second objective and pacing')
        self.store.report();return ident

    def native(self,task,ident,candidate,probe):
        bundle,gate=ContinuousRunner.native(self,task,ident,candidate,probe)
        if task['id']==MAP_TASK['id'] and gate.get('passed'):
            objects=json.loads((bundle/'captures/scene-transforms.json').read_text())['objects']
            for key,check in [('prop_clone_parity',inspect_alley_clones(objects)),('door_layer_order',inspect_door_layers(objects))]:
                gate['scoped_facts'][key]=check
                if not check['passed']:gate.update(passed=False,failure=(gate.get('failure') or [])+check['failure'])
            atomic(bundle/'scoped-gate.json',gate)
        return bundle,gate

    def qualify(self,task,ident,candidate,probe):
        self.store.set(stage='native-scoped-gate',last_valid_replay=probe);self.store.report()
        bundle,gate=qualify_extension_native(self,task,ident,candidate,probe)
        if not gate.get('passed'):return bundle,gate,gate
        self.store.set(stage='fresh-scoped-critique');self.store.report()
        review=self.review(task,ident,bundle,gate)
        if not review.get('ok') or review.get('verdict')!='PASS':return bundle,gate,review
        return bundle,gate,None

    def record_rejection(self,task,ident,candidate,feedback):
        key=failure_key({k:feedback[k] for k in ('failure','compile_errors','verdict','fixes') if k in feedback})
        streak=self.store.get('failure_streak',0)+1 if key==self.store.get('failure_key') else 1
        self.store.set(feedback=feedback,failure_key=key,failure_streak=streak,
            task_failures=self.store.get('task_failures',0)+1,stage='rejected')
        self.store.event('bounded-scope-rejected',candidate=candidate,task=task['outcome'],round=ident,
            original_counters_preserved=True,feedback=feedback)
        self.store.report()

    def local_street_source(self,ident):
        files=Files(self.project,self.store);edits=ReadBoundEdits(files,True)
        allowed=set(STREET_PATHS)
        def complete(path):
            count=len(files.path(path).read_text().splitlines())
            return ''.join(edits.read('',dict(path=path,start_line=start,line_count=300))['content']
                           for start in range(1,count+1,300))
        source=complete(PATH)
        extra=self.project/'Assets/Game/ConnectedStreet.cs'
        if extra.exists():source+='\nConnectedStreet.cs:\n'+complete('Assets/Game/ConnectedStreet.cs')
        def scoped(fn):
            def call(action,fields):
                if fields['path'] not in allowed:raise ValueError('Use exactly one of these project-relative paths: '+', '.join(STREET_PATHS))
                content=fields.get('new',fields.get('content',''))
                limit=160 if 'content' in fields else 120
                if len(content.splitlines())>limit:raise ValueError('Save one smaller edit, at most '+str(limit)+' lines')
                return fn(action,fields)
            return call
        self.c.update(output_tokens=8192,model_timeout_seconds=400)
        self.store.set(stage='local-second-street-source');self.store.report()
        s={'type':'string'}
        path_schema={'type':'string','enum':list(STREET_PATHS)}
        result=self.model.session('builder',ident+'-street-source',
            'You are the sole local Qwen game author. Save a small original topology change now; no mission or replay authoring in this role.',
            json.dumps(SECOND_TASK)+'\nACTUAL PREVIOUS FEEDBACK:\n'+json.dumps(self.store.get('feedback',{}))[:12000]+
            '\nONLY VALID PROJECT-RELATIVE TOOL PATHS: '+json.dumps(list(STREET_PATHS))+
            '\nEXACT CURRENT WORLD SOURCE, already read and hash-bound for replacement:\n'+source+
            '\nMake one small saved tool edit per response. You may revise WorldColliders directly or create one compact '
            'ConnectedStreet.cs helper and call it from WorldColliders.Install. No need to reread unchanged source. '
            'The existing east end has BOTH AddWall collider and a visible AlleyEndWall with collider, plus a '
            'decorative FenceBarrier; account for all three at the interior opening. Remove only obsolete boundary '
            'segments and replace with new visible outer boundaries. Preserve all other colliders and accepted tests. '
            'Keep each replacement at most120lines and a new helper at most160lines; do not rewrite the entire file. Submit finish_source after saving. '
            'A separate role will propose a short physical replay from saved source; no ten-minute replay here.',
            [tool('read_file','Read exact current allowed source.',{'path':path_schema,'start_line':{'type':'integer'},'line_count':{'type':'integer'}},['path']),
             tool('replace_text','Save one exact unique bounded replacement.',{'path':path_schema,'old':s,'new':s}),
             tool('create_file','Save one new compact source module.',{'path':path_schema,'content':s}),
             tool('finish_source','Describe the actually saved geometry and junction.',{'summary':s})],
            {'read_file':scoped(edits.read),'replace_text':scoped(edits.replace),'create_file':scoped(edits.create),
             'finish_source':lambda _,f:dict(ok=True,summary=f['summary'][:2000])},turns=6,reasoning_effort='low')
        candidate=self.checkpoint_source('Local Qwen: second connected street source / '+ident)
        if self.store.get('second_street_attempts')==1 and candidate==self.store.get('source_checkpoint'):
            raise Halt('Second-street role saved no source; no native expansion claim')
        self.store.set(source_checkpoint=candidate,candidate_commit=candidate)
        self.store.event('local-second-street-source-saved',candidate=candidate,result=result,
            final_game_accepted=False,cloud_game_code_authored=False)
        return candidate

    def local_street_replay(self,ident):
        paths=[PATH,'Assets/Game/ConnectedStreet.cs','Assets/Game/VehicleInteraction.cs']
        source='\n\n'.join(p+'\n'+(self.project/p).read_text() for p in paths if (self.project/p).exists())
        source+='\nBOOTSTRAP/WALKER:\n'+(self.project/'Assets/Game/Bootstrap.cs').read_text().split('    public class Follow')[0]
        self.c.update(output_tokens=8192,model_timeout_seconds=400)
        self.store.set(stage='local-second-street-replay');self.store.report()
        result=self.model.session('replay-author',ident+'-street-replay',
            'You are local Qwen submitting a short normal-input traversal of the saved second street. No code edits.',
            json.dumps(SECOND_TASK)+'\nUse finish_task with summary,duration,input_steps,captures. '
            'Every step is {start,end,keys}; keys W/A/S/D/E. Keep0..4input-free, no R reset; duration16..150, '
            '>=4increasing captures before duration. Hold E>=0.25seconds within the real car boarding radius. '
            'First walk6m beyond the union and physically return, then drive6m beyond and return. '
            'Use the proven original alley approach as a starting point, adapting the outward and return travel '
            'to the NEW saved geometry. Include outside foot/car, junction and return captures. '
            'No courier completion, ten-minute mission or idle padding is required by this scope. '
            'Call finish_task immediately when the route is ready.\nACCEPTED SHORT ALLEY INPUTS:\n'+
            json.dumps(self.store.get('saved_door_probe'))+'\nACTUAL FAILURE FEEDBACK:\n'+
            json.dumps(self.store.get('feedback',{}))[:12000]+'\nCURRENT SOURCE:\n'+source,
            [finish_tool()],{'finish_task':lambda _,f:validate_submission(f,SECOND_TASK)},
            turns=2,reasoning_effort='low')
        if not result.get('scenario'):raise Halt('Second-street replay supplied no complete bounded tool submission')
        return result['scenario']

    def work(self):
        probe=self.accepted_probe();self.store.set(saved_door_probe=probe)
        ident=self.begin(DOOR_TASK,'saved-door-requalification')
        bundle,gate,failure=self.qualify(DOOR_TASK,ident,SOURCE,probe)
        if failure:
            self.record_rejection(DOOR_TASK,ident,SOURCE,failure)
            raise Halt('Saved door did not qualify; accepted connector and local correction preserved')
        promote_qualified_extension(self,DOOR_TASK,bundle,gate,json.loads((bundle/'critic.json').read_text()))
        self.store.set(saved_door_accepted=True,feedback={},task_design=SECOND_TASK['instructions'])
        return self.advance_second_street()

    def advance_second_street(self,start_attempt=1,last_attempt=3):
        for attempt in range(start_attempt,last_attempt+1):
            ident=self.begin(SECOND_TASK,'local-second-street-source')
            self.store.set(second_street_attempts=attempt)
            candidate=self.local_street_source(ident)
            probe=self.local_street_replay(ident)
            bundle,gate,failure=self.qualify(SECOND_TASK,ident,candidate,probe)
            if failure:
                self.record_rejection(SECOND_TASK,ident,candidate,failure);continue
            record=promote_qualified_extension(self,SECOND_TASK,bundle,gate,json.loads((bundle/'critic.json').read_text()))
            return self.continue_after_street(record)
        raise Halt('Bounded changed second-street attempts exhausted; preserve evidence and accepted connector')

    def continue_after_street(self,record):
        self.store.set(second_connected_street=record,task_design=
                'Second street passed scoped native traversal. Next create a meaningful second objective beyond '
                'the original core and extend actual connected travel/objectives/pursuit toward8-12minutes. '
                'Preserve regressions. Use original facade window assemblies with relative depths intact for '
                'bounded presentation work. No waiting/idle padding and no final-quality claim from this scope.',
                feedback={'accepted_second_street':record})
        return ContinuousRunner.work(self)


if __name__=='__main__':raise SystemExit(main(SavedDoor))
