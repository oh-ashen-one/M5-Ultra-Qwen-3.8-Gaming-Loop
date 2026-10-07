#!/usr/bin/env python3
"""Local pixel/geometry-driven repair of the added Armed hint's card fit."""
from qualify_qwen_capacity import CapacityAuthor
from submit_counter_exfil_parts import between,writes_shared_signals
from implement_counter_exfil import TASK,HUD,validate_source
from finish_counter_exfil_parts import MISSION,ACCEPTED
from resume_three_day_queue import main
from loop_controller.core import Files,Halt,atomic,sha
from loop_controller.model import tool
from loop_controller.delivery_policy import HARD_CAP_EPOCH

SOURCE='ff3564295c6f8cb97cade915e089abf19056743a'
PRIOR='q0171-3601cd2a'

def validate_boundary(old):
    expected=dict(status='paused',controller_pid=None,owned_process=None,current_round=PRIOR,
        source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,task_index=7,task_failures=24,
        failure_streak=1,diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,
        blocker='Halt: Counter-Exfil source failed the unchanged healthy route prerequisite')
    gate=old.get('counter_exfil_probe_outcome',{}).get('old_healthy',{})
    failures={'MissionBoard-text-outside-card','actual-interception-objective-not-rendered',
        'interception-live-objective-not-rendered','objective-not-compact'}
    if (any(old.get(k)!=v for k,v in expected.items()) or old.get('counter_exfil_hud_fit_attempted')
            or set(gate.get('failure',[]))!=failures or gate.get('compile_errors')
            or gate.get('build_exit')!=0 or not gate.get('scene_inventory',{}).get('passed')):
        raise Halt('Require the actual added Armed-line presentation failure and unchanged game source/history')

class RepairCounterHudFit(CapacityAuthor):
    def validate_recovery(self,old):
        validate_boundary(old);self.prior=old['counter_exfil_source_outcome']
        self.resume_capacity=self.priority_resume=self.transport_recovery=self.admission_recovery=False
    def recovery_settings(self):
        return dict(counter_exfil_hud_fit_attempted=True,recovery_route='local-measured-armed-hud-fit',
            recovery_change='Keep the exact old ending plus one Armed hint. Native geometry and pixels prove the fifth line exceeds its card; locally fit that state and shorten its hint. Preserve old layout in other states and every gameplay method.')
    def work(self):
        ident=self.begin(TASK,'local-counter-exfil-armed-hud-fit');files=Files(self.project,self.store)
        original={p:files.path(p).read_text() for p in (HUD,MISSION)}
        hint=between(original[MISSION],'        public string HudLine','        public string Objective')
        protected={str(p.relative_to(self.project)):sha(p.read_bytes()) for p in self.project.rglob('*')
            if p.is_file() and p.suffix in ('.cs','.shader','.fbx','.blend','.py') and str(p.relative_to(self.project)) not in original}
        def save(action,fields):
            hud=fields['hud_source'];line=fields['hint_property']
            if len(hud.encode())>18000 or len(hud.splitlines())>260 or len(line.encode())>1400 or len(line.splitlines())>25:
                raise ValueError('Return only the bounded complete HUD and selected HudLine property')
            if not line.lstrip().startswith('public string HudLine'):raise ValueError('Replace only HudLine')
            for value in (hud,line):
                if writes_shared_signals(value):raise ValueError('Do not write shared signals')
            tail=original[HUD][original[HUD].index('        string DeathBoard('):]
            if tail not in hud:raise ValueError('Preserve exact death handling and every remaining legacy helper')
            accessor=original[HUD][original[HUD].index('        static string ReadStr('):]
            validate_source(HUD,hud.replace('using System.Reflection;','').replace(accessor,''));validate_source(MISSION,line)
            if not hud.endswith('\n'):hud+='\n'
            if not line.endswith('\n'):line+='\n'
            files.edit(action+'-hud',HUD,sha(original[HUD].encode()),old=original[HUD],new=hud)
            files.edit(action+'-hint',MISSION,sha(original[MISSION].encode()),old=hint,new=line)
            if any(sha(files.path(p).read_bytes())!=h for p,h in protected.items()):raise Halt('Protected gameplay or assets changed')
            candidate=self.checkpoint_source('Local Qwen: fit Armed hint while preserving the old ending and other HUD states')
            self.store.set(source_checkpoint=candidate);self.store.report()
            return dict(ok=True,local_authored=True,candidate=candidate,changed_files=[HUD,MISSION],native_verified=False)
        self.c.update(working_context_tokens=65536,output_tokens=16384,model_timeout_seconds=600)
        frame=self.store.root/'evidence'/(PRIOR+'-old-healthy')/'captures/frame-007.png'
        result=self.model.session('builder',ident+'-hud-fit-source',
            'You are local Qwen, sole gameplay/presentation author. Save the precise measured Armed HUD fit correction now.',
            'Actual Unity build succeeds and the old route completes at75.433seconds,28HP. The attached77s image '
            'and projection show your fifth Armed hint below the card: text bottom.75927, card bottom.76754 '
            '(top.94701), same in live4:3/capture16:9. Preserve ALL FOUR lines of the original interception '
            'ending verbatim and append exactly one compact Armed hint <=40characters, with coupe distance '
            'and E/F actions. Keep font/size, top anchor, colours, camera, reticle and original gameplay. '
            'Expand/reposition only the existing card backing downward while Armed to contain five lines; '
            'restore exact original card geometry for every other state, including death and R. The card '
            'must remain <=.24 viewport height and within screen. Its original clone position is '
            '(0,-.125,.025), scale(1.5,.36,.01); retain this geometry outside live Armed. Store the existing '
            'clone transform and adjust that same card, no second board or new assets. Preserve installation '
            'and all old objective/death fallbacks. Return COMPLETE MissionDirectorHud.cs plus ONLY the '
            'selected HudLine property. Do not rewrite commentary or other methods. Native acceptance '
            'will explicitly recognize the authorized fifth line only while genuinely Armed with old '
            'clean completion; all geometric/readability limits and old-ending content remain enforced.\n'
            'CURRENT HUD:\n'+original[HUD]+'\nEXACT MISSION PROPERTY:\n'+hint,
            [tool('finish_source','Save complete HUD and only the selected compact hint property.',
                {'hud_source':{'type':'string'},'hint_property':{'type':'string'}})],{'finish_source':save},
            images=[('ACTUAL FAILED ARMED HUD,77 seconds; preserve the four old ending lines',frame)],turns=3,reasoning_effort='xhigh')
        atomic(self.store.root/'evidence'/(ident+'-hud-fit-source.json'),result)
        if not result.get('ok'):raise Halt('Preserve local source and the measured Armed HUD fit failure')
        self.store.set(counter_exfil_hud_fit_result=result,counter_exfil_source_outcome=dict(self.prior,candidate=result['candidate'],hud_fit=result));self.store.report()
        raise Halt('Counter-Exfil Armed HUD fit saved; unload idle inference and requalify original route and new inputs')

if __name__=='__main__':raise SystemExit(main(RepairCounterHudFit))
