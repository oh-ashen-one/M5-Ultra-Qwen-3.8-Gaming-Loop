"""Exact replay submission schema; validate before starting an expensive native build."""
import json
from .continuous_checks import validate_proposed
from .model import tool, typed_arguments

FIELDS = {
    'summary': {'type': 'string'},
    'duration': {'type': 'number'},
    'input_steps': {'type': 'array', 'items': {'type': 'object', 'properties': {
        'start': {'type': 'number'}, 'end': {'type': 'number'},
        'keys': {'type': 'array', 'items': {'type': 'string'}}},
        'required': ['start', 'end', 'keys'], 'additionalProperties': False}},
    'captures': {'type': 'array', 'items': {'type': 'number'}},
}

MISSION_EXAMPLE = {
    'summary': 'Proposed normal-input courier route; native success remains unverified.',
    'duration': 20,
    'input_steps': [
        {'start':4,'end':4.6,'keys':['S']},
        {'start':5,'end':6.07,'keys':['W']},
        {'start':6.3,'end':6.99,'keys':['D']},
        {'start':7.2,'end':7.45,'keys':['F']},
        {'start':8,'end':8.65,'keys':['W']},
        {'start':8.9,'end':9.34,'keys':['D']},
        {'start':9.6,'end':9.85,'keys':['E']},
        {'start':10.3,'end':14.2,'keys':['W']},
        {'start':15,'end':15.25,'keys':['F']},
    ],
    'captures': [3.2,4.8,7.1,7.7,10,14.5,15.5,18],
}


def finish_tool():
    return tool('finish_task', 'Submit all four required fields; no source edit in this replay-only role.', FIELDS)


def validate_submission(fields, task):
    value = typed_arguments({'name':'finish_task','arguments':fields}, [finish_tool()])
    if not value['summary'].strip():
        raise ValueError('summary must describe the actual proposed replay')
    replay = validate_proposed({'duration':value['duration'], 'steps':value['input_steps'],
                                'captures':value['captures']}, task['maximum'], task['coverage'])
    if 'failure_retry' in task.get('checks',[]):
        resets=[s for s in replay['steps'] if 'R' in s['keys']]
        if not any(s['start']>r['end'] and 'F' in s['keys'] for r in resets for s in replay['steps']):
            raise ValueError('Failure/retry requires ordinary R reset followed by later F interactions; native evidence must prove actual failure first')
    return {'ok':True, 'summary':value['summary'][:2000], 'scenario':replay}


def replay_guide(task):
    return ('Call finish_task with exactly summary:string, duration:number, input_steps:array, captures:array. '
            'Each input step is {start:number,end:number,keys:[key names]}. Use input_steps, not steps. '
            'Seconds are from launch. Keep t=0..4 input-free. Duration must be16..'+str(task['maximum'])+
            ' seconds; start>=4,end<=duration. At least4 strictly increasing capture times before duration. '
            'Use W/A/S/D,E,F,R,Mouse0 as appropriate; press E/F/R for at least0.25s to make input observable. '
            'Include walking away from the parcel by at least1m more than initial distance, returning within1.5m, '
            'F pickup, E entry, real driving and F delivery at the stationary destination. '
            'This syntax-valid example is test infrastructure, not claimed successful gameplay. Adapt timings to '
            'current source and actual feedback; do not redesign game code to detect this replay:\n'+json.dumps(MISSION_EXAMPLE))
