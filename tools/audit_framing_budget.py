#!/usr/bin/env python3
"""CPU-only token/setting audit. Emits counts and checks, never private response text."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from jinja2 import Environment, StrictUndefined
from tokenizers import Tokenizer

from loop_controller.model import MODEL, response_accounting, tool


def functions(path,names,namespace):
    selected=[n for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef) and n.name in names]
    if {n.name for n in selected}!=set(names):raise ValueError('Installed public helper names changed')
    exec(compile(ast.Module(body=selected,type_ignores=[]),'installed-public-settings-helpers','exec'),namespace)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('run-dir','source-root','resident-settings'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();config=json.loads((a.run_dir/'private-config.json').read_text())
    tokenizer_path=Path(config['tokenizer_file'])
    assert hashlib.sha256(tokenizer_path.read_bytes()).hexdigest()==config['tokenizer_sha256']
    tokenizer=Tokenizer.from_file(str(tokenizer_path));tokenizer.no_padding();tokenizer.no_truncation()
    count=lambda text:len(tokenizer.encode(text,add_special_tokens=False).ids)
    namespace={'Any':Any}
    utils=a.source_root/'api/utils.py';settings_source=a.source_root/'model_settings.py'
    functions(utils,['merge_reasoning_effort_chat_template_kwargs'],namespace)
    functions(settings_source,['forced_ct_keys','merge_chat_template_request_kwargs'],namespace)
    raw=json.loads(a.resident_settings.read_text())['models'][MODEL]
    settings=SimpleNamespace(**{'forced_ct_kwargs':None,'chat_template_kwargs':None,'enable_thinking':None,'preserve_thinking':None,**raw})
    def reject(message):raise ValueError(message)
    template=tokenizer_path.parent/'chat_template.jinja'
    env=Environment(undefined=StrictUndefined);env.globals['raise_exception']=reject
    rendered_template=env.from_string(template.read_text())
    checks=[]
    for effort in ('low','medium','xhigh'):
        requested=namespace['merge_reasoning_effort_chat_template_kwargs']({'enable_thinking':True,'preserve_thinking':True},effort)
        merged=namespace['merge_chat_template_request_kwargs'](settings,requested)
        assert merged['reasoning_effort']==effort and merged['enable_thinking'] and merged['preserve_thinking']
        rendered=rendered_template.render(messages=[{'role':'user','content':'Synthetic inert fixture.'}],
            tools=[tool('record_fixture','Inert fixture.',{'value':{'type':'string'}})],add_generation_prompt=True,**merged)
        assert rendered.endswith('<think>\n')
        if effort=='low':assert 'Keep your thinking brief and focused' in rendered
        if effort=='xhigh':assert 'Please think carefully through the task' in rendered
        checks.append({'effort':effort,'request_overrides_resident_default':True,'thinking_prefix_open':True,'preserve_thinking':True})
    rows=[]
    for folder in sorted((a.run_dir/'private/sessions').iterdir()):
        if not (folder.name.startswith(('r0002-','r0003-','r0004-')) and '-micro-edit-' in folder.name
                or folder.name in ('framing-budget-camera','framing-budget-camera-review')):continue
        for path in sorted(folder.glob('response-*.json')):
            response=json.loads(path.read_text());choice=response['choices'][0];message=choice['message']
            usage=response.get('usage',{})
            row={'session':folder.name,'response_index':int(path.stem.split('-')[-1]),'finish_reason':choice.get('finish_reason'),
                 'usage':{k:usage[k] for k in ('prompt_tokens','completion_tokens','total_tokens','total_time','completion_tokens_details') if k in usage},
                 'accounting':response_accounting(message,count)}
            row['tool_argument_retokenized_tokens']=sum(count(f['function']['arguments'] if isinstance(f['function']['arguments'],str)
                else json.dumps(f['function']['arguments'],separators=(',',':'))) for f in message.get('tool_calls',[]) or [])
            rows.append(row)
    print(json.dumps({'scope':'CPU-only; local counts and public template/settings checks; no inference or private text exported',
        'caveat':'Server completion_tokens is authoritative total. Retokenized fields/arguments are diagnostics, not an exact server-side reasoning/output split.',
        'model':MODEL,'template_sha256':hashlib.sha256(template.read_bytes()).hexdigest(),
        'runtime_sources':{str(path.relative_to(a.source_root)):hashlib.sha256(path.read_bytes()).hexdigest() for path in (utils,settings_source)},
        'resident_default_effort':raw.get('chat_template_kwargs',{}).get('reasoning_effort'),
        'forced_template_keys':sorted(namespace['forced_ct_keys'](settings)),
        'effective_request_checks':checks,'requests':rows},indent=2))

if __name__=='__main__':main()
