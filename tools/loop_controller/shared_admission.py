"""Yield the resident lease while a real shared waiter/holder finishes."""
import contextlib
import time
from .core import Halt, atomic, now, read_json

CAPACITY_ERRORS = {'Existing shared GPU waiters have priority',
                   'Existing GPU holder requires coordination', 'Shared GPU capture slots occupied'}


@contextlib.contextmanager
def admitted(factory, guard, store, request, lease, engine_timeout,
             sleeper=time.sleep, monotonic=time.monotonic, clock=time.time, recheck_seconds=30):
    # The request already yielded our resident's locks. Keep that handoff in
    # place while others run; never remove their queue/holder records.
    if not 1 <= recheck_seconds <= 30:raise ValueError('Admission recheck must be between1and30seconds')
    deadline = monotonic() + 300
    stage = store.get('stage'); waiting = False
    with contextlib.ExitStack() as acquired:
        while True:
            guard()
            current = read_json(request)
            if current.get('lease_id') != lease['lease_id']:
                raise Halt('Engine admission lease identity changed')
            try:
                acquired.enter_context(factory())
                break
            except (RuntimeError, BlockingIOError) as error:
                if not isinstance(error, BlockingIOError) and str(error) not in CAPACITY_ERRORS:
                    raise
                if monotonic() >= deadline:
                    raise Halt('Capacity wait: shared queue did not admit the engine within300seconds') from error
                waiting = True
                store.set(status='capacity-wait', stage='capacity-wait', capacity_resume_stage=stage,
                    blocker='Capacity wait: shared reservation unavailable; preserve other owners',
                    capacity_check_utc=now(), capacity_recheck_seconds=recheck_seconds)
                store.report(); sleeper(min(recheck_seconds, max(0, deadline-monotonic())))
        # Start the bounded engine runtime deadline only after slot admission.
        # The project cap and all resource/STOP guards remain independent.
        current = read_json(request)
        if current.get('lease_id') != lease['lease_id']:
            raise Halt('Engine admission lease identity changed')
        current['expires_epoch'] = clock() + engine_timeout + 90
        atomic(request, current)
        if waiting:
            store.event('shared-slot-admission-restored', resume_stage=stage)
        store.set(status='running', stage=stage, blocker=None, capacity_resume_stage=None)
        store.report()
        yield
