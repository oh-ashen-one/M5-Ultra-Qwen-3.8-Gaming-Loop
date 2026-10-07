#!/usr/bin/env python3
"""Explicit disposable adapter check: existing original art, native green/red play."""
import argparse
import json
from pathlib import Path
import shutil

from loop_controller.core import Store, atomic, now, read_json, seal, sha
from loop_controller.adapters import Engines, Machine, evaluate_runtime
from loop_controller.runner import ROOT, initialize_project, scenario_for


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run-dir",type=Path,required=True)
    p.add_argument("--config",type=Path,required=True)
    p.add_argument("--allow-smoke",action="store_true")
    p.add_argument("--reuse-fixture",type=Path)
    a=p.parse_args()
    if not a.allow_smoke:p.error("Explicit bounded fixture authorization is required")
    if a.run_dir.exists():p.error("Use a fresh fixture directory; preserve failed attempts")
    s=Store(a.run_dir);c=read_json(a.config)
    machine=Machine(c,s);engines=Engines(c,s,machine,ROOT)
    project=a.run_dir/"fixture"
    if a.reuse_fixture:
        shutil.copytree(a.reuse_fixture,project)
        if sha((project/"Art/smoke.py").read_bytes()) != sha((ROOT/"diagnostics/connector-2026-10-05/asset_scene.py").read_bytes()):
            raise RuntimeError("Reused original fixture source changed")
        provenance=read_json(project/"Assets/Resources/Generated/smoke/provenance.json")
        for item in provenance["files"]:
            if sha((project/item["path"]).read_bytes())!=item["sha256"]:
                raise RuntimeError("Reused fixture asset changed")
        # Raw authoring files stay outside Assets, avoiding Unity's implicit
        # Blender conversion on top of the already exported FBX.
        original=project/"ArtSources/smoke";original.mkdir(parents=True,exist_ok=True)
        shutil.move(project/"Assets/Resources/Generated/smoke/source.blend",original/"source.blend")
        shutil.move(project/"Assets/Resources/Generated/smoke/provenance.json",original/"prior-export-provenance.json")
    else:
        initialize_project(project)
    shutil.copyfile(ROOT/"tests/fixtures/Bootstrap.cs",project/"Assets/Game/Bootstrap.cs")
    shutil.copyfile(ROOT/"diagnostics/connector-2026-10-05/asset_scene.py",project/"Art/smoke.py")
    receipt={"started_utc":now(),"scope":"disposable controller fixture, not Chicago game output",
             "game_started":False,"fixture_author":"cloud infrastructure","asset_author":"unchanged prior local Qwen original Blender source"}
    try:
        art={"ok":True,"scope":"reused verified prior original export"} if a.reuse_fixture else engines.blender(project,"Art/smoke.py","smoke-art")
        receipt["art"]={k:v for k,v in art.items() if k!="diagnostic"}
        if not art["ok"]:raise RuntimeError("Existing original Blender fixture failed: "+art["diagnostic"])
        scenario=scenario_for("foundation")
        bundle=a.run_dir/"evidence/native-green"
        green=engines.unity(project,bundle,scenario,"disposable-fixture")
        receipt["green"]=green
        atomic(a.run_dir/"receipt.json",receipt)
        if not green["passed"]:raise RuntimeError("Native green fixture did not pass")
        app=bundle/"build/ChicagoLocalSlice.app"
        binary=list((app/"Contents/MacOS").glob("*"))[0]
        red=a.run_dir/"evidence/native-red";red.mkdir(parents=True)
        atomic(red/"scenario.json",scenario)
        code=machine.execute("unity-red",[str(binary),"-batchmode","-force-metal","-logFile","-",
            "--loop-output",str(red),"--loop-scenario",str(red/"scenario.json"),"--loop-capture-id","native-red",
            "--fixture-stationary"],bundle/"project",red,110,protected=[red/"scenario.json"])
        result=evaluate_runtime(red,scenario,code,"native-red")
        receipt["red"]=result
        if result["passed"] or "input-driven-player-movement" not in result.get("failure",[]):
            raise RuntimeError("Deliberately disabled movement did not produce the expected red gate")
        receipt["status"]="PASS"
        receipt["evidence_sha256"]=seal(a.run_dir/"evidence",{"scope":"native adapter green/red qualification"})
    except Exception as error:
        receipt.update(status="FAILED",error=type(error).__name__+": "+str(error))
    receipt["finished_utc"]=now();atomic(a.run_dir/"receipt.json",receipt)
    print(json.dumps(receipt,indent=2),flush=True)
    return 0 if receipt["status"]=="PASS" else 1

if __name__=="__main__":raise SystemExit(main())
