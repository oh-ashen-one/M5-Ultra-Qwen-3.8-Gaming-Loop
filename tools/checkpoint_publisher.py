#!/usr/bin/env python3
"""Lightweight checkpoint transport through existing controller GitHub auth.

This is not a game owner or cloud-monitoring schedule. It fetches one explicitly
configured M5 game branch and pushes that same branch without force or merges.
No credential is copied to the M5. Configuration and logs remain private.
"""
import argparse
import json
import os
from pathlib import Path
import shlex
import subprocess
import time


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config",type=Path,required=True)
    p.add_argument("--once",action="store_true")
    a=p.parse_args();c=json.loads(a.config.read_text())
    if not c["branch"].startswith("game/chicago-") or any(ch not in "abcdefghijklmnopqrstuvwxyz0123456789-/" for ch in c["branch"]):
        raise ValueError("Only an explicitly named Chicago game task branch may be published")
    destination="https://github.com/oh-ashen-one/M5-Ultra-Qwen-3.8-Gaming-Loop.git"
    root=Path(c["mirror"])
    if not root.exists():subprocess.run(["git","init","--bare",str(root)],check=True,stdout=subprocess.DEVNULL)
    env={**os.environ,"GIT_SSH_COMMAND":shlex.join(c["ssh_command"])}
    deadline=time.monotonic()+c.get("wall_hours",13)*3600
    while time.monotonic()<deadline and not (root.parent/"PUBLISHER_STOP").exists():
        try:
            subprocess.run(["git","--git-dir",str(root),"fetch",c["source_url"],
                            c["branch"]+":refs/heads/"+c["branch"]],env=env,check=True,capture_output=True,timeout=60)
            commit=subprocess.check_output(["git","--git-dir",str(root),"rev-parse",c["branch"]],text=True).strip()
            subprocess.run(["git","--git-dir",str(root),"push",destination,
                            "refs/heads/"+c["branch"]+":refs/heads/"+c["branch"]],check=True,capture_output=True,timeout=60)
            receipt={"status":"published","commit":commit,"branch":c["branch"],"published_epoch":time.time(),"transport":"existing authenticated controller; no M5 account credential"}
            command="import json,os,sys;from pathlib import Path;p=Path(sys.argv[1]);t=p.with_suffix('.tmp');t.write_text(sys.argv[2]+'\\n');t.replace(p)"
            remote=shlex.join(["/usr/bin/python3","-B","-c",command,c["receipt_path"],json.dumps(receipt)])
            subprocess.run([*c["ssh_command"],c["ssh_target"],remote],check=True,capture_output=True,timeout=30)
            print(json.dumps(receipt),flush=True)
        except subprocess.SubprocessError as error:
            print(json.dumps({"status":"publication-pending","error":type(error).__name__,"at":time.time()}),flush=True)
            if a.once:return 2
        if a.once:return 0
        time.sleep(60)
    return 0

if __name__=="__main__":raise SystemExit(main())
