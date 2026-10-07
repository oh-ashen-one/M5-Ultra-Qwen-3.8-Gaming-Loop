#!/usr/bin/env python3
"""Fresh local actual-pixel review after complete single-incident native proof."""
import json
from qualify_qwen_capacity import CapacityAuthor
from probe_counter_exfil import ACCEPTED,TASK
from resume_three_day_queue import main
from continue_game_queue import validate_scoped_review
from review_player_death_integration import REGRESSIONS
from loop_controller import counter_exfil_death_checks as counter_death
from loop_controller import player_death_checks as old_death
from loop_controller.core import Halt,atomic,read_json,sha,now
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.model import tool
from loop_controller.runner import git
from loop_controller.visual_context import contract,TARGETS

def require_native(result,source):
    if result.get('candidate')!=source:raise Halt('Native source mismatch')
    prior=result.get('prior_native',{})
    if prior.get('candidate')!=source:raise Halt('Original native source mismatch')
    for name in ('old_healthy','activation_escape','success'):
        item=prior.get(name,{})
        if (item.get('candidate')!=source or not item.get('gate',{}).get('passed')
                or not item.get('native',{}).get('passed') or item['native'].get('candidate_commit')!=source
                or item['native'].get('build_id')!=item.get('build_id') or not item.get('build_id') or not item.get('evidence')):
            raise Halt('Missing successful actual native prerequisite '+name)
    for name in ('success_continuity','contact'):
        item=result.get(name,{})
        if item.get('candidate')!=source or not item.get('passed') or not item.get('build_id') or not item.get('evidence'):
            raise Halt('Missing independent physical proof '+name)
    for key,cases in [('counter_deaths',counter_death.CASES),('old_deaths',old_death.CASES)]:
        items=result.get(key,[])
        if (len(items)!=len(cases) or {x.get('case') for x in items}!=set(cases)
                or any(x.get('candidate')!=source or not x.get('passed') or not x.get('native',{}).get('passed')
                    or x['native'].get('candidate_commit')!=source or x['native'].get('build_id')!=x.get('build_id')
                    or not x.get('build_id') or not x.get('evidence') for x in items)):
            raise Halt('Require every source-matched death boundary: '+key)
    regress=result.get('regressions',{})
    items=regress.get('regressions',[])
    if (not regress.get('passed') or len(items)!=len(REGRESSIONS) or {x.get('test') for x in items}!=REGRESSIONS
            or any(not x.get('gate',{}).get('passed') or x['gate'].get('candidate_commit')!=source for x in items)):
        raise Halt('Require all ten unchanged source-matched regressions')

def validate_boundary(old):
    expected=dict(status='paused',controller_pid=None,owned_process=None,last_playable_checkpoint=ACCEPTED,
        task_index=7,task_failures=24,failure_streak=1,diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,
        counter_exfil_negatives_attempted=True,
        blocker='Halt: One Counter-Exfil incident passes physical success, contact/death negatives and original regressions; source-matched pixel review required')
    if any(old.get(k)!=v for k,v in expected.items()) or old.get('counter_exfil_visual_review_attempted'):
        raise Halt('Require complete stopped incident qualification and unchanged accepted history')
    require_native(old.get('counter_exfil_negatives_outcome',{}),old.get('source_checkpoint'))

class ReviewCounterIncident(CapacityAuthor):
    def validate_recovery(self,old):
        validate_boundary(old);self.source=old['source_checkpoint'];self.native_result=old['counter_exfil_negatives_outcome']
        self.native_path=self.store.root/'evidence'/(old['current_round']+'-counter-negatives.json')
        if read_json(self.native_path)!=self.native_result:raise Halt('Native ledger and preserved artifact disagree')
        self.resume_capacity=self.priority_resume=self.transport_recovery=self.admission_recovery=False
    def recovery_settings(self):
        return dict(counter_exfil_visual_review_attempted=True,recovery_route='fresh-local-complete-incident-pixel-review',
            recovery_change='Fresh local xhigh critic sees source-matched Armed, combat, actual success, escape, active/failed death and reset images plus the target. No edit tools. Only scoped PASS after all native proof can promote this one incident; no next-design expansion or final-game claim.')
    def work(self):
        ident=self.begin(TASK,'fresh-local-counter-exfil-pixel-review')
        prior=self.native_result['prior_native'];deaths={x['case']:x for x in self.native_result['counter_deaths']}
        selected=[('armed',prior['old_healthy'],7),('combat-before',prior['success'],3),
            ('combat-after',prior['success'],5),('complete',prior['success'],7),
            ('escape',prior['activation_escape'],4),('active-death',deaths['active-runners'],1),
            ('failed-death',deaths['failed-escape'],1),('reset',deaths['active-runners'],3)]
        images=[];times={};proof={self.native_path:sha(self.native_path.read_bytes())}
        for name,item,index in selected:
            bundle=self.store.root/'evidence'/item['evidence'];frame=bundle/'captures'/f'frame-{index:03d}.png'
            label=name+'/'+frame.name;t=read_json(bundle/'captures/scenario.json')['captures'][index];times[label]=t
            images.append((f'ACTUAL NATIVE {label}; t={t} seconds',frame))
            for p in (frame,bundle/'captures/scenario.json',bundle/'captures/trace.jsonl',bundle/'gate.json'):
                proof[p]=sha(p.read_bytes())
        images.append(('CHICAGO TARGET: aspiration, not native output',self.refs/TARGETS[0]))
        packet=contract(images,[TARGETS[0]],8)
        self.c.update(working_context_tokens=98304,output_tokens=16384,model_timeout_seconds=600)
        facts=dict(candidate=self.source,physical_success=self.native_result['success_continuity']['facts'],
            real_contact_release=self.native_result['contact']['release'],all_four_new_and_six_old_death_cases_passed=True,
            original_healthy_and_ten_regressions_passed=True,death_cases_use_declared_external_health_zero=True,
            full_game_art_and_ten_minute_pacing_unfinished=True)
        result=self.model.session('critic',ident+'-incident-critic',
            'You are a fresh local visual critic. Inspect the supplied actual native pixels and submit one scoped verdict.',
            'Judge only this ONE Counter-Exfil incident: old ending plus compact readable Armed hint; '
            'legible actual targets, coupe, aim/reticle and live HP/pin counts; two standard enemies gone '
            'after actual shots with lead still alive/pinned; coherent foot completion; readable specific '
            'escape failure; immediate readable death/R instructions during Active and after a prior '
            'specific failure; living reset without stale text. Check all supplied text lies on its card '
            'and remains visible. Native traces independently prove nine unit-damage camera-aligned '
            'shots, distinct kills, continuous physical pin and real foot crossing, contact-loss clearing, '
            'four new/six old death gates and ten regressions. Stills alone cannot prove those dynamics '
            'or natural lethal damage. Cite the unique case/frame labels or authoritative times. '
            'Return PASS/FIX/UNVERIFIED for this scoped incident, with at most five prioritized concrete '
            'fixes and explicit visible limitations. Original rough art, animation, lighting/audio and '
            'ten-minute pacing remain unfinished; do not accept final quality or inflate duration. '
            'There is no editing or planning tool; call submit_review now.\nFACTS:'+json.dumps(facts)+
            '\nAUTHORITATIVE IMAGE TIMES:'+json.dumps(times),
            [tool('submit_review','Record the scoped actual-pixel verdict.',{'verdict':{'type':'string'},
                'summary':{'type':'string'},'fixes':{'type':'array','items':{'type':'string'}}})],
            {'submit_review':lambda _,f:validate_scoped_review(f,list(times),times)},images=images,
            visual_contract=packet,turns=3,reasoning_effort='xhigh')
        if (any(sha(p.read_bytes())!=h for p,h in proof.items()) or git(self.repo,'rev-parse','HEAD')!=self.source
                or git(self.repo,'status','--porcelain')):raise Halt('Source or actual evidence changed during read-only review')
        accepted=bool(result.get('ok') and result.get('verdict')=='PASS')
        artifact=dict(candidate=self.source,native_artifact=self.native_path.name,
            native_sha256=proof[self.native_path],review=result,frames=packet['records'],
            scoped_accepted=accepted,final_game_accepted=False,ten_minute_gameplay_proven=False)
        atomic(self.store.root/'evidence'/(ident+'-counter-visual-review.json'),artifact)
        self.store.set(counter_exfil_visual_review_outcome=artifact);self.store.report()
        if not accepted:raise Halt('Preserve complete incident native proof; actual local visual review needs focused follow-up')
        self.store.set(counter_exfil_scoped_acceptance=dict(candidate=self.source,accepted_utc=now(),
            scope='One Counter-Exfil incident: actual shooting/live physical pin/foot exit, contact/death/reset boundaries and scoped HUD pixels',
            evidence=ident+'-counter-visual-review.json',native_evidence=self.native_path.name,
            prior_playable_checkpoint=ACCEPTED,final_game_accepted=False),last_playable_checkpoint=self.source)
        self.store.event('scoped-counter-exfil-checkpoint-promoted',candidate=self.source,
            preserved_task_index=7,preserved_task_failures=24,preserved_failure_streak=1)
        self.store.report()
        raise Halt('One Counter-Exfil incident accepted after native and actual-pixel proof; preserve this checkpoint and report remaining full-game limitations')

if __name__=='__main__':raise SystemExit(main(ReviewCounterIncident))
