#!/usr/bin/env python3
"""One-request liveness watchdog; no inference, engine launch or automatic restart."""
import argparse
import datetime
import fcntl
import http.cookiejar
import json
import os
from pathlib import Path
import signal
import time
import urllib.request

from loop_controller.core import atomic,now,read_json


def stalled(previous,current,minimum_age=180):
    """Require two successful unchanged observations of the identical request."""
    if not previous or previous.get('request_id')!=current.get('request_id'):return False
    a,b=previous.get('generated_tokens'),current.get('generated_tokens')
    ages=[previous.get('last_activity_age_seconds'),current.get('last_activity_age_seconds')]
    return (isinstance(a,int) and a>0 and a==b and
            all(isinstance(v,(int,float)) and v>=minimum_age for v in ages))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run-dir',type=Path,required=True)
    p.add_argument('--controller-pid',type=int,required=True)
    p.add_argument('--controller-start',type=float,required=True)
    p.add_argument('--round',required=True)
    p.add_argument('--request-id',required=True)
    p.add_argument('--session-id',required=True)
    p.add_argument('--turn',type=int,required=True)
    a=p.parse_args();os.umask(0o077)
    import psutil
    c=read_json(a.run_dir/'private-config.json');base=c['endpoint'].removesuffix('/v1').rstrip('/')
    if base!='http://127.0.0.1:8027':raise RuntimeError('Only the existing local service is allowed')
    token=Path(c['token_file']).read_text().strip()
    jar=http.cookiejar.CookieJar();opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    req=urllib.request.Request(base+'/admin/api/login',
        data=json.dumps({'api_key':token,'remember':False}).encode(),headers={'Content-Type':'application/json'})
    with opener.open(req,timeout=5) as f:assert json.load(f).get('success')
    path=a.run_dir/'request-progress-watch.json';previous=None;samples=[]
    response=a.run_dir/'private/sessions'/a.session_id/('response-%03d.json'%a.turn)
    with (a.run_dir/'request-progress-watch.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        while True:
            s=read_json(a.run_dir/'status.json')
            if response.exists() or s.get('controller_pid')!=a.controller_pid or s.get('current_round')!=a.round:
                atomic(path,dict(status='finished',utc=now(),reason='Response saved or original owner boundary ended',samples=samples));return
            owner=psutil.Process(a.controller_pid)
            if abs(owner.create_time()-a.controller_start)>.01:raise RuntimeError('Controller PID identity changed')
            try:
                with opener.open(base+'/admin/api/activity',timeout=5) as f:value=json.load(f)
                candidates=[v for m in value.get('active_models',{}).get('models',[]) for v in m.get('generating',[])
                            if v.get('request_id')==a.request_id]
                if len(candidates)!=1:
                    atomic(path,dict(status='finished',utc=now(),reason='Original generating request no longer present',samples=samples));return
                current=candidates[0]
            except Exception as error:
                # A failed observation cannot establish a hung request.
                previous=None
                atomic(path,dict(status='observation-unavailable',utc=now(),error_type=type(error).__name__,samples=samples))
                time.sleep(20);continue
            samples=(samples+[dict(utc=now(),**current)])[-8:]
            atomic(path,dict(status='observing',watchdog_pid=os.getpid(),utc=now(),controller_pid=a.controller_pid,
                request_id=a.request_id,stall_age_seconds=180,recheck_seconds=20,samples=samples))
            if stalled(previous,current):
                # Recheck exact source owner and completion immediately before the
                # sole possible action. A healthy/progressing request is untouched.
                fresh=read_json(a.run_dir/'status.json')
                if (response.exists() or fresh.get('controller_pid')!=a.controller_pid or
                    fresh.get('current_round')!=a.round or abs(owner.create_time()-a.controller_start)>.01):return
                atomic(path,dict(status='verified-token-stall',utc=now(),controller_pid=a.controller_pid,
                    request_id=a.request_id,samples=samples,action='Graceful stop of exact owned controller; no restart'))
                owner.send_signal(signal.SIGTERM);return
            previous=current;time.sleep(20)


if __name__=='__main__':main()
