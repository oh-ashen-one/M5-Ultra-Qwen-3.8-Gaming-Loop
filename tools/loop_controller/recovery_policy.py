"""Finite changed-strategy native recovery; never admits runtime or approval faults."""
import hashlib
import json

MAX_MAP_ATTEMPTS=3
MAP_REPLAY_FAILURES=frozenset({
    'foot-new-space-not-traversed','vehicle-new-space-not-traversed',
    'foot-outside-duration','vehicle-outside-duration',
    'foot-physical-return-missing','vehicle-physical-return-missing',
    'foot-collision-continuity','vehicle-collision-continuity',
    'foot-discontinuous-traversal','vehicle-discontinuous-traversal',
    'walking-not-grounded','vehicle-rendered-support','rendered-pavement-support',
    'foot-outside-capture-missing','vehicle-outside-capture-missing'})


def support_repair_scope(gate, rows, driving_start):
    """Later driving parameters cannot repair already-observed prefix faults."""
    failures=gate.get('failure',[])
    support=gate.get('scoped_facts',{}).get('rendered_walking_support',{})
    scopes=[]
    if 'rendered-pavement-support' in failures and any(
            r.get('time',float('inf'))<driving_start for r in support.get('first_uncovered',[])):
        scopes.append('walking-prefix')
    if 'vehicle-rendered-support' in failures:
        surfaces=support.get('surfaces',[])
        if surfaces and any(r.get('mode')=='vehicle' and r.get('time',float('inf'))<driving_start
                and not any(s['min'][0]<=r['vehicle'][0]<=s['max'][0]
                    and s['min'][2]<=r['vehicle'][2]<=s['max'][2]
                    and abs(s['max'][1]-r['vehicle'][1])<.5 for s in surfaces) for r in rows):
            scopes.append('vehicle-source')
    return scopes


def recovery_route(gate,attempt_count):
    failures=gate.get('failure')
    eligible=(gate.get('passed') is False and gate.get('build_exit')==0 and
        gate.get('player_exit')==0 and not gate.get('compile_errors') and
        isinstance(failures,list) and bool(failures) and
        set(failures)<=MAP_REPLAY_FAILURES)
    if not eligible:return 'report-blocker'
    return 'changed-strategy' if attempt_count<MAX_MAP_ATTEMPTS else 'report-blocker'


def replay_identity(scenario):
    # Captures or summary changes alone cannot masquerade as changed gameplay.
    data={'duration':scenario['duration'],'steps':scenario['steps']}
    return hashlib.sha256(json.dumps(data,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def admit_strategy(scenario,diagnosis,history):
    if len(history)>=MAX_MAP_ATTEMPTS:raise ValueError('Map recovery attempt budget exhausted')
    if not isinstance(diagnosis,str) or len(diagnosis.strip())<30:
        raise ValueError('State a concrete diagnosis and changed physical route in summary')
    identity=replay_identity(scenario)
    if any(row['replay_sha256']==identity for row in history):
        raise ValueError('Unchanged physical replay rejected; use the latest actual failure evidence')
    return {'attempt':len(history)+1,'replay_sha256':identity,'diagnosis':diagnosis[:2000]}
