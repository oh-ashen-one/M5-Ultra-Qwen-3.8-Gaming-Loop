#!/usr/bin/env python3
"""One authorized low-effort/thinking-on local edit, then real native framing evidence."""
import argparse
import json
import os
from pathlib import Path
import signal
import time

from inspect_and_repair_grounding import grounding_scenario, summarize
from loop_controller.core import Files, Halt, atomic, exclusive, now, read_json, seal, sha
from loop_controller.model import tool
from loop_controller.runner import Runner, git
from loop_controller.small_edits import SelectedEdit


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run-dir',type=Path,required=True)
    p.add_argument('--authorize-framing-repair',action='store_true')
    a=p.parse_args()
    if not a.authorize_framing_repair:p.error('Explicit current framing-repair authorization required')
    os.umask(0o077)
    c=read_json(a.run_dir/'private-config.json');r=Runner(a.run_dir,c);s=r.store
    if s.get('controller_pid') or s.get('status')!='paused':raise Halt('Expected stopped sole owner')
    known=read_json(a.run_dir/'evidence/grounding-3/grounding-gate.json')
    if not known.get('stationary_grounded') or git(r.repo,'rev-parse','HEAD')!=known['candidate_commit']:
        raise Halt('Preserve and start from the proven grounded source')
    if s.get('framing_budget_attempt'):raise Halt('This setting hypothesis already ran; inspect its evidence')
    progress=s.get('last_accepted_epoch',s.get('started_epoch'))
    deadline=min(time.time()+20*60,s.get('overall_deadline_epoch'),progress+c['no_accepted_progress_minutes']*60)
    if deadline<=time.time():raise Halt('Existing run deadline expired')
    def stop(*_):raise Halt('Bounded framing deadline or explicit stop')
    signal.signal(signal.SIGALRM,stop);signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
    signal.alarm(max(1,int(deadline-time.time())))
    with exclusive(a.run_dir/'controller.lock'):
        s.set(controller_pid=os.getpid(),status='running',blocker=None,stage='framing-budget-edit',
              framing_budget_attempt=now(),framing_budget_deadline_epoch=deadline)
        s.event('cloud-infrastructure-intervention',action='One camera assignment with measured bounds and save-first tool',
                settings_change={'builder_effort':'low','enable_thinking':True,'output_tokens':8192,'critic_effort':'xhigh'},
                attempts=1,prior_failures_preserved=True,original_deadlines_unchanged=True,
                authorization='Parent requested task-appropriate supported reasoning and one or two local edits followed by a native frame')
        try:
            r.recover();r.model.ready();r.machine.guard()
            files=Files(r.project,s);path='Assets/Game/Bootstrap.cs'
            lines=files.path(path).read_text().splitlines(keepends=True)
            start=next(i for i,line in enumerate(lines) if 'class Follow :' in line)
            choices=[i for i,line in enumerate(lines) if i>=start and 'public Vector3 offset =' in line]
            if len(choices)!=1:raise Halt('Expected one exact Follow.offset assignment')
            index=choices[0];edit=SelectedEdit(files,path,index+1,index+1,1)
            observed=read_json(a.run_dir/'evidence/grounding-3/world-observations.json')
            measured={key:observed[key] for key in ('largest_street_renderers','player_visual_bounds')}
            measured['stationary_player']=observed['stationary_first']['player']
            c.update(output_tokens=8192,model_timeout_seconds=300)
            prompt=('Save one replacement assignment through edit_selected_span now. Change ONLY Follow.offset. '
                'The current camera starts inside the facade: facade spans world Z -8 to 0, while the player starts at Z 1.7 '
                'and forward walking moves toward +Z. Put the camera on the open +Z side so it looks back toward the upright player '
                'and existing building; select a compact third-person height and distance. Preserve Follow rotation/look-at logic, '
                'all physics, visual scale and scene instances. No tiling, loops, new objects or other edits. '
                'Thinking remains enabled at low effort for this single assignment. The required outcome is one saved C# line, not a plan. '
                '\nEXACT RELEVANT CAMERA CLASS:\n'+''.join(lines[start:])+
                '\nSELECTED ONE LINE:\n'+edit.old+'\nMEASURED WORLD BOUNDS:\n'+json.dumps(measured))
            result=r.model.session('builder','framing-budget-camera',
                'You are the local C# author. Briefly solve one assignment and save it through the tool first.',prompt,
                [tool('edit_selected_span','Save exactly one replacement C# line; full-file hash and selection are enforced.',{'content':{'type':'string'}})],
                {'edit_selected_span':lambda action,f:edit.apply(action,f['content'])},turns=1,reasoning_effort='low')
            if sha(files.path(path).read_bytes())==edit.before:
                s.event('setting-hypothesis-stopped',outcome=result,action='Inspect request/template/tool formatting before any further request')
                raise Halt('Setting hypothesis saved no edit; inspect safe accounting and tool formatting, do not repeat capped requests')
            candidate=r.checkpoint_source('Local Qwen: measured camera assignment with low effort and thinking enabled')
            s.set(source_checkpoint=candidate,candidate_commit=candidate,bounded_no_progress_streak=0,
                  last_source_progress_utc=now(),last_source_progress_epoch=time.time(),stage='native-framing-budget')
            s.event('source-progress',candidate=candidate,prior_grounded_checkpoint=known['candidate_commit'],accepted_checkpoint_unchanged=True)
            bundle=a.run_dir/'evidence/framing-budget-camera'
            gate=r.engines.unity(r.project,bundle,grounding_scenario(),candidate)
            observations=summarize(bundle) if (bundle/'captures/scene-transforms.json').exists() else {'stationary_grounded':None}
            atomic(bundle/'world-observations.json',observations);gate['stationary_grounded']=observations['stationary_grounded']
            if not gate['stationary_grounded']:
                failures=gate.get('failure') or [];failures=failures if isinstance(failures,list) else [failures]
                gate.update(passed=False,failure=failures+['stationary-grounding-preflight'])
            atomic(bundle/'grounding-gate.json',gate)
            s.set(latest_evidence=str(bundle.relative_to(a.run_dir)),feedback=gate,
                  latest_captures=[str(x.relative_to(a.run_dir)) for x in sorted((bundle/'captures').glob('frame-*.png'))])
            if not gate['passed']:raise Halt('Changed candidate failed native gate; preserve it for diagnosis')
            captured=seal(bundle/'captures',{'candidate':candidate,'scope':'native evidence before independent critic'})
            def review(_,fields):
                if fields['verdict'] not in ('PASS','FIX','UNVERIFIED'):raise ValueError('Use PASS, FIX or UNVERIFIED')
                return {'ok':True,**fields}
            c.update(output_tokens=4096,model_timeout_seconds=200)
            reviewed=r.model.session('critic','framing-budget-camera-review',
                'You are a fresh local visual critic. Judge the supplied actual native frames only.',
                'The native stationary grounding and horizontal walking gate passed. Is the upright player clearly framed with '
                'readable existing street/buildings before and after walking? PASS only this narrow framing bar, not game polish. '
                'Use FIX for void, obstruction or unreadable layout. Submit a verdict and one observable next fix of at most 35 words.',
                [tool('submit_review','Submit actual-image verdict.',{'verdict':{'type':'string'},'next_fix':{'type':'string'}})],
                {'submit_review':review},images=[('Actual native stationary frame',bundle/'captures/frame-000.png'),
                ('Actual native post-walk frame',bundle/'captures/frame-003.png')],turns=1,reasoning_effort='xhigh')
            from loop_controller.core import verify_seal
            verify_seal(bundle/'captures',captured);atomic(bundle/'basic-framing-review.json',reviewed)
            s.set(mechanical_grounded_checkpoint=candidate,mechanical_grounded_evidence=str(bundle.relative_to(a.run_dir)),
                  feedback={**gate,'framing_review':reviewed},status='paused',stage='framing-budget-reviewed',
                  blocker='Saved local edit and native evidence ready for inspection; authorized adaptive continuation remains pending')
            s.event('framing-budget-qualified',candidate=candidate,gate_passed=True,framing_verdict=reviewed.get('verdict'),
                    larger_game_task_accepted=False)
        except Exception as error:
            s.set(status='paused',blocker=type(error).__name__+': '+str(error))
            s.event('stopped',error_type=type(error).__name__,message=str(error))
        finally:
            signal.alarm(0);candidate=r.checkpoint_source('Preserve bounded framing setting experiment')
            s.set(controller_pid=None,source_checkpoint=candidate);s.report()
    return 0

if __name__=='__main__':raise SystemExit(main())
