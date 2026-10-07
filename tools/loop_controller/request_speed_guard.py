"""Bound one owned request using measured token progress; never restart a service."""
import contextlib
import http.cookiejar
import json
import os
import signal
import threading
import time
import urllib.request

from .core import Halt, atomic, now, read_json


def sustained_slow(samples, floor, window=60):
    if len(samples) < 2:
        return False
    last = samples[-1]
    eligible = [s for s in samples[:-1] if s['request_id'] == last['request_id']
                and last['elapsed'] - s['elapsed'] >= window]
    if not eligible:
        return False
    first = eligible[-1]
    tokens = last['generated_tokens'] - first['generated_tokens']
    return tokens >= 0 and tokens / (last['elapsed'] - first['elapsed']) < floor


@contextlib.contextmanager
def request_guard(model, request_id, private, turn):
    policy = model.config.get('runtime_performance_guard')
    if not policy:
        yield
        return
    stop = threading.Event()
    failed = []
    started = time.monotonic()
    pid = os.getpid()
    import psutil
    identity = psutil.Process(pid).create_time()
    initial = model.store.status()
    round_id = initial.get('current_round')
    if initial.get('controller_pid') != pid:
        raise Halt('Speed guard requires the current controller owner')
    floor = max(8.0, float(policy['validated_text_tps']) * .2)
    path = private / ('speed-watch-%03d.json' % turn)
    response = private / ('response-%03d.json' % turn)
    samples = []

    def observation(status, **fields):
        atomic(path, dict(utc=now(), status=status, controller_pid=pid,
            controller_request_id=request_id, minimum_decode_tps=floor,
            sustained_window_seconds=60, maximum_request_seconds=600,
            samples=samples[-16:], **fields))

    def halt(reason):
        current = read_json(model.store.root / 'status.json')
        if (stop.is_set() or response.exists() or current.get('controller_pid') != pid
                or current.get('current_round') != round_id
                or abs(psutil.Process(pid).create_time() - identity) > .01):
            return
        failed.append(reason)
        observation('stopped-for-diagnosis', reason=reason)
        os.kill(pid, signal.SIGTERM)

    def watch():
        jar = http.cookiejar.CookieJar()
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
        logged_in = False
        slow_observations = 0
        while not stop.wait(5):
            elapsed = time.monotonic() - started
            if elapsed >= 600:
                halt('Owned model request exceeded the ten-minute artifact-progress bound')
                return
            try:
                if not logged_in:
                    req = urllib.request.Request(model.base + '/admin/api/login',
                        data=json.dumps({'api_key': model.token, 'remember': False}).encode(),
                        headers={'Content-Type': 'application/json'})
                    with opener.open(req, timeout=5) as stream:
                        logged_in = bool(json.load(stream).get('success'))
                    if not logged_in:
                        raise RuntimeError('Read-only activity login unavailable')
                with opener.open(model.base + '/admin/api/activity', timeout=5) as stream:
                    activity = json.load(stream)
                active = [v for m in activity.get('active_models', {}).get('models', [])
                          for v in m.get('generating', [])]
                if len(active) != 1:
                    samples.clear()
                    slow_observations = 0
                    observation('waiting-for-single-generating-request')
                    continue
                row = active[0]
                count = row.get('generated_tokens')
                if not isinstance(count, int) or count <= 0:
                    continue
                if samples and samples[-1]['request_id'] != row['request_id']:
                    samples.clear()
                    slow_observations = 0
                samples.append(dict(elapsed=elapsed, request_id=row['request_id'], generated_tokens=count))
                samples[:] = samples[-20:]
                slow_observations = slow_observations + 1 if sustained_slow(samples, floor) else 0
                observation('observing', slow_observations=slow_observations)
                if slow_observations >= 2:
                    halt('Sustained decode fell below 20% of the validated short-control rate; diagnose before retry')
                    return
            except Exception as error:
                samples.clear()
                slow_observations = 0
                observation('observation-unavailable', error_type=type(error).__name__)
    thread = threading.Thread(target=watch, name='owned-request-speed-watch', daemon=True)
    observation('armed')
    thread.start()
    try:
        yield
    except BaseException as error:
        if failed:
            raise Halt(failed[0]) from error
        raise
    finally:
        stop.set()
        thread.join(timeout=11)
        if not failed:
            observation('finished', elapsed_seconds=round(time.monotonic() - started, 3))
