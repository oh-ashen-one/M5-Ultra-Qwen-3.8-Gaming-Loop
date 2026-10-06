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
