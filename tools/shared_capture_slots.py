"""Acquire actual shared locks; authorized coexistence reserves one task slot."""
import contextlib
import fcntl
import json
import os
from pathlib import Path


@contextlib.contextmanager
def capture_slots(base, metadata, external_renderers=0, coexistence=False, guard=None):
    base = Path(base)
    if coexistence and guard is None:
        raise ValueError('Authorized coexistence requires a live resource/ownership guard')
    def check():
        if (base/'PAUSED').exists(): raise RuntimeError('Shared GPU admission paused')
        if guard is not None and guard() is False:
            raise RuntimeError('Existing GPU holder requires coordination')
    check()
    for name in ('locks','holders','queue'): (base/name).mkdir(parents=True,exist_ok=True)
    if not coexistence:
        if any((base/'queue').iterdir()): raise RuntimeError('Existing shared GPU waiters have priority')
        if any((base/'holders').glob('*.json')): raise RuntimeError('Existing GPU holder requires coordination')
    holder=base/'holders'/(str(os.getpid())+'.json')
    if holder.exists(): raise RuntimeError('This process already owns a shared capture record')
    owned=False
    with contextlib.ExitStack() as stack:
        perf=stack.enter_context((base/'locks/perf.lock').open('a+'))
        # An exclusive performance job remains an absolute admission barrier.
        fcntl.flock(perf,fcntl.LOCK_SH|fcntl.LOCK_NB)
        slots=[]; required=1 if coexistence else min(2,external_renderers+1)
        for index in range(2):
            fd=(base/'locks'/f'capture.{index}.lock').open('a+')
            try: fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError: fd.close();continue
            stack.enter_context(fd);slots.append(index)
            if len(slots)==required: break
        if len(slots)!=required: raise RuntimeError('Shared GPU capture slots occupied')
        check()
        value={**metadata,'pid':os.getpid(),'slot':str(slots[0]),'reserved_slots':slots,
               'external_renderer_count':external_renderers,
               'admission_policy':'authorized-shared-coexistence' if coexistence else 'legacy-exclusive-capture'}
        try:
            with holder.open('x') as f: json.dump(value,f,indent=2);f.write('\n')
            owned=True
            yield base
        finally:
            if owned: holder.unlink()
