"""Compact actual gate evidence without losing failures or attack attribution."""
from copy import deepcopy


def compact_rows(value):
    if isinstance(value,dict):return {k:compact_rows(v) for k,v in value.items()}
    if isinstance(value,list):
        if len(value)>12:
            return {'sample_count':len(value),'first_samples':[compact_rows(v) for v in value[:3]],
                'last_samples':[compact_rows(v) for v in value[-3:]],
                'note':'Intermediate samples omitted from this review summary; original trace is preserved.'}
        return [compact_rows(v) for v in value]
    return value


def critic_evidence(gate):
    value={k:deepcopy(v) for k,v in gate.items() if k not in ('regressions','diagnostic')}
    regression=gate.get('regressions')
    if regression:
        value['regressions']={k:regression[k] for k in ('passed','failure') if k in regression}
        value['regressions']['tests']=[]
        for entry in regression.get('regressions',[]):
            g=entry['gate'];item={'test':entry['test'],**{k:g[k] for k in
                ('passed','failure','candidate_commit','scope','combat_contract') if k in g}}
            if 'failure_retry' in g.get('scoped_facts',{}):item['failure_retry']=g['scoped_facts']['failure_retry']
            value['regressions']['tests'].append(item)
    return compact_rows(value)


def require_combat_contracts(gate):
    records=gate.get('combat_contracts',[]) or [v['gate']['combat_contract']
        for v in gate.get('regressions',{}).get('regressions',[]) if 'combat_contract' in v['gate']]
    scopes={v.get('scope'):v for v in records if v.get('passed') and v.get('candidate')==gate.get('candidate_commit')}
    return (set(scopes)>={'foot','wall','driving'} and
        scopes['driving'].get('facts',{}).get('longest_continuous_escape_seconds',0)>=2.0)
