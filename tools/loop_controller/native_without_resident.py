"""Native-only admission while the task's inference service is deliberately off."""
import contextlib
import os
from pathlib import Path
import socket
import time
import uuid

from .core import Halt, atomic, exclusive, read_json
from .shared_admission import admitted


def inference_process(info):
    return (info.get('name') == 'omlx-server' or any(
        word in ('mlx_vlm.server', 'mlx_lm.server') or Path(word).name in ('omlx', 'llama-server')
        for word in info.get('cmdline') or []))


def require_unloaded(machine):
    from engine_admission import complete_process_scan
    import psutil
    machine.guard()
    for process in complete_process_scan(['pid', 'name', 'cmdline'], psutil):
        if process.pid != os.getpid() and inference_process(process.info):
            raise Halt('Native-only mode requires inference unloaded; preserve the other owner')


@contextlib.contextmanager
def engine(machine, label, timeout):
    """Keep all resource/slot guards; replace an absent resident's handoff only."""
    import psutil
    from warmup_resident import gpu_admission
    coord = Path(machine.c['coordination_dir'])
    request, ack = coord / 'engine-request.json', coord / 'engine-ack.json'
    with exclusive(coord / 'request.lock'), socket.socket() as reservation:
        require_unloaded(machine)
        # The resident startup must bind this dedicated loopback port before
        # loading weights. Reserve it exclusively, without listening or address
        # reuse, during native work. A lingering socket fails closed.
        try:
            reservation.bind(('127.0.0.1', 8027))
        except OSError as error:
            raise Halt('Native-only inference reservation unavailable; no engine launched') from error
        if request.exists() or ack.exists():
            raise Halt('Preserve an existing engine handoff before native-only admission')
        lease = dict(lease_id=uuid.uuid4().hex, controller_pid=os.getpid(),
            controller_start=psutil.Process().create_time(), expires_epoch=time.time()+min(1500, timeout+390),
            label=label, mode='native-only-model-unloaded')
        atomic(request, lease)
        def guard():
            require_unloaded(machine)
            if read_json(request).get('lease_id') != lease['lease_id']:
                raise Halt('Native-only engine ownership changed')
        try:
            observed = machine.snapshot()
            external = len(observed['decision']['active_renderer_pids'])
            with admitted(lambda: gpu_admission('chicago-native-only-'+label, external,
                    authorized_shared_coexistence=machine.c.get('authorized_shared_coexistence', False),
                    guard=guard), guard, machine.store, request, lease, timeout,
                    recheck_seconds=machine.c.get('native_admission_recheck_seconds',30)):
                machine.store.event('native-without-resident-admitted', label=label,
                    inference_unloaded=True, original_resource_guards=True)
                yield
        finally:
            if request.exists() and read_json(request).get('lease_id') == lease['lease_id']:
                request.unlink()
