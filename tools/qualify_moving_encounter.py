"""Same-owner native moving encounter qualification and next local scope design."""
import json
from continue_game_queue import validate_scoped_review, review_evidence_seal
from loop_controller.core import Halt,atomic,read_json,verify_seal
from loop_controller.model import tool
from loop_controller.interception_checks import probes,inspect_interception
from loop_controller.consolidated_hud import inspect_hud
from loop_controller.relay_contract import inspect_relay,scenarios
from loop_controller.continuous_tasks import TASKS
from resume_hud_presentation_polish import inspect_polish


def checked(bundle,gate,case):
    if not gate.get('passed'): return gate
    rows=[json.loads(x) for x in (bundle/'captures/trace.jsonl').read_text().splitlines()]
    path=bundle/'captures/aim-shots.jsonl'
    events=[json.loads(x) for x in path.read_text().splitlines()] if path.exists() else []
    values=dict(interception=inspect_interception(rows,events,case),hud=inspect_hud(rows),polish=inspect_polish(rows))
    if case in ('positive','escape'): values['relay']=inspect_relay(rows,'positive')
    failures=sorted({item for check in values.values() for item in (check.get('failure') or [])})
    gate.update(passed=not failures,failure=failures or None,**values)
    atomic(bundle/'moving-encounter-gate.json',gate)
    return gate


def review(r,ident,candidate,positive,escape,gates):
    selected=[(positive,2),(escape,3),(positive,7),(positive,8)]
    images=[];times={};sealed=[]
    for bundle in [positive,escape]:
        sealed.append((bundle/'captures',review_evidence_seal(bundle/'captures',candidate,'moving-encounter-'+bundle.name.rsplit('-',1)[-1])))
    for bundle,index in selected:
        p=bundle/'captures'/f'frame-{index:03d}.png'
        t=read_json(bundle/'captures/scenario.json')['captures'][index]
        if not p.exists(): raise Halt('Required actual encounter review frame missing')
        times[p.name]=t
        images.append(('ACTUAL NATIVE '+p.name+'; case='+bundle.name.rsplit('-',1)[-1]+'; t='+str(t)+' seconds',p))
    facts={case:{k:gate['interception'][k] for k in ('activations','completions','escapes','resets','movement_metres',
        'actual_new_target_damage','other_live_rivals_after_lethal','secondary_target_isolation_qualified')}
        for case,gate in gates.items() if case in ('positive','escape')}
    r.c.update(output_tokens=8192,model_timeout_seconds=600)
    r.store.set(stage='fresh-moving-encounter-critique');r.store.report()
    result=r.model.session('critic',ident+'-critic',
        'You are a fresh local visual critic. Judge the actual new moving-target encounter only.',
        'Native current-source positive, live escape, no-handoff, whole reset, relay wrong-order/timeout and '
        'all ten old gameplay regressions passed. Read provided measured facts. The first image shows actual '
        'camera-aimed combat; second is the separate no-fire moving/escape case; third is the positive ending; '
        'fourth is whole reset. Judge readable target framing, movement direction, coherent objective/health, '
        'ending/failure/reset presentation, and new blocking regressions. Prior rough character/art/street '
        'quality remains explicitly unfinished; a scope PASS is not full game acceptance. No new assets or '
        'ten-minute result is claimed. Do not call validation waiting added content. Use PASS/FIX/UNVERIFIED '
        'and at most3..5 prioritized concrete fixes. Cite actual supplied filenames/times. '
        'SHOT/STATE FACTS:'+json.dumps(facts)+'\nAUTHORITATIVE TIMES:'+json.dumps(times),
        [tool('submit_review','Return the fresh scoped native visual verdict.',{'verdict':{'type':'string'},
            'summary':{'type':'string'},'fixes':{'type':'array','items':{'type':'string'}}})],
        {'submit_review':lambda _,f:validate_scoped_review(f,list(times),times)},images=images,turns=2,reasoning_effort='xhigh')
    for path,digest in sealed: verify_seal(path,digest)
    atomic(positive/'critic.json',result);return result


def next_design(r,ident,gate):
    fields=['next_actions','exact_physical_scope','source_interfaces','failure_retry_and_ending','native_acceptance','measured_pacing_limits']
    r.store.set(stage='local-connected-mission-expansion-design');r.store.report()
    r.c.update(output_tokens=3072,model_timeout_seconds=240)
    complete=gate['interception']['completions'][0]
    context='\n\n'.join(name+'\n'+(r.project/'Assets/Game'/name).read_text() for name in
        ['InterceptionMission.cs','RouteMission.cs'])
    def save(_,data):
        if set(data)!=set(fields) or any(not isinstance(x,str) or not 40<=len(x)<=1300 for x in data.values()):
            raise ValueError('Six concrete fields,40..1300characters each')
        return dict(ok=True,**data)
    result=r.model.session('planner',ident+'-next-expansion',
        'You are local Qwen, substantive game designer. Define the next meaningful connected mission increment.',
        f'The new actual moving interception completes at{complete:.3f}seconds from ordinary game start. '
        'Earlier progression reached59.633seconds; validation ends95seconds only to test reset. Target remains '
        '540..660seconds of varied play, not empty laps, idle time or more renamed F boxes. Define one next '
        'substantial connected objective: reuse original coupe/props and existing driving/foot/combat APIs, '
        'with exact new physical rectangle and connector if required. Existing real space is coreX-1..6/Z-2..30, '
        'alleyX6..22/Z8..20, eaststreetX22..60/Z8..28; barriers exist. Never treat invisible400x400ground as '
        'rendered playable space or closed facades as interiors. No new downloaded asset or generic primitive '
        'art. Specify actual install/HUD hooks and separate owned state, failure/retry/ending, reach/collision '
        'and positive/red proof. Keep earlier mechanics and accepted checkpoint. Distinguish estimates from '
        'measured duration and identify remaining route/variation dependencies. Write concise final decisions '
        'only; call submit_plan now.\nACTUAL APIs:\n'+context,
        [tool('submit_plan','Save the next implementable connected gameplay scope.',{k:{'type':'string'} for k in fields})],
        {'submit_plan':save},turns=1,reasoning_effort='low')
    atomic(r.store.root/'evidence'/(ident+'-next-expansion.json'),result)
    r.store.set(next_connected_expansion=result);r.store.report()
    if not result.get('ok'): raise Halt('Next connected mission design needs bounded diagnosis')
    raise Halt('Moving encounter qualified and next connected scope saved; seal physical/action acceptance and continue implementation')


def qualify(r,ident,candidate,escape,escape_gate,original,positive_probe=None,prior_escape=False):
    proposals=probes(original);gates={};bundles={'escape':escape}
    if positive_probe is not None: proposals['positive']=positive_probe
    for case in ('escape','positive','inactive'):
        r.store.set(stage='native-moving-encounter-'+case);r.store.report()
        bundle=escape if case=='escape' else r.store.root/'evidence'/(ident+'-'+case)
        gate=escape_gate if case=='escape' else r.engines.unity(r.project,bundle,proposals[case],candidate)
        if case=='escape' and prior_escape:
            if (gate.get('candidate_commit')!=candidate or not gate.get('passed') or
                not gate.get('interception',{}).get('passed') or gate['interception'].get('case')!='escape'):
                raise Halt('Prior escape evidence must already pass on this exact source')
        else: gate=checked(bundle,gate,case)
        gates[case]=gate;bundles[case]=bundle
        r.store.set(moving_encounter_native={k:dict(evidence=str(bundles[k].relative_to(r.store.root)),
            passed=v.get('passed'),failure=v.get('failure')) for k,v in gates.items()});r.store.report()
        if not gate.get('passed'): raise Halt('Moving encounter '+case+' needs measured diagnosis: '+json.dumps(gate.get('failure')))
    r.store.set(stage='moving-encounter-original-regressions');r.store.report()
    legacy=r.regress(TASKS[7],ident,candidate)
    if not legacy.get('passed'): raise Halt('Moving encounter changed a previous gameplay contract')
    bundle=r.store.root/'evidence'/(ident+'-relay-wrong-timeout')
    gate=r.engines.unity(r.project,bundle,scenarios(original)['wrong-timeout'],candidate)
    if gate.get('passed'):
        rows=[json.loads(x) for x in (bundle/'captures/trace.jsonl').read_text().splitlines()]
        values=[inspect_relay(rows,'wrong-timeout'),inspect_interception(rows,[],'inactive'),inspect_hud(rows),inspect_polish(rows)]
        gate['checks']=values;gate['passed']=all(v['passed'] for v in values)
        atomic(bundle/'moving-relay-regression.json',gate)
    if not gate.get('passed'): raise Halt('Moving encounter changed relay failure/reset or HUD contracts')
    verdict=review(r,ident,candidate,bundles['positive'],escape,gates)
    result=dict(candidate=candidate,evidence=str(bundles['positive'].relative_to(r.store.root)),
        native_cases={k:v.get('passed') for k,v in gates.items()},legacy_regressions=legacy,
        review=verdict,accepted=bool(verdict.get('ok') and verdict.get('verdict')=='PASS'),
        secondary_target_isolation_qualified=True,final_game_accepted=False)
    atomic(bundles['positive']/'moving-encounter-outcome.json',result)
    r.store.set(moving_encounter_outcome=result);r.store.report()
    if not result['accepted']: raise Halt('Moving encounter native proof recorded; continue measured local visual fixes')
    next_design(r,ident,gates['positive'])
