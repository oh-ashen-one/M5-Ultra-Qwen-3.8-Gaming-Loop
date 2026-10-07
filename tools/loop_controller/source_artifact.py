"""Validate completed public source responses without replaying partial messages."""
from .core import Halt


def complete_csharp(response,max_lines=400,max_bytes=32000):
    choices=response.get('choices',[])
    if len(choices)!=1 or choices[0].get('finish_reason')!='stop':
        raise Halt('C# source requires a completed public response; no partial application')
    message=choices[0].get('message',{})
    source=message.get('content')
    if message.get('tool_calls') or not isinstance(source,str):
        raise Halt('Require public C# final content without a tool envelope')
    source=source.strip()
    for language in ('csharp','cs'):
        start='```'+language+'\n'
        if source.startswith(start) and source.endswith('\n```'):
            source=source[len(start):-4];break
    if (not source or any(marker in source for marker in ['<think>','</think>','```','<tool_call>'])
            or len(source.splitlines())>max_lines or len(source.encode())>max_bytes):
        raise Halt('Require one bounded complete C# artifact without reasoning or markers')
    # This gate is provenance/transport validation. Only the real Unity compiler
    # and immutable native acceptance establish valid behavior.
    return source+'\n'
