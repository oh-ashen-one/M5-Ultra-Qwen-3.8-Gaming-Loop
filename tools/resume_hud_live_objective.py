#!/usr/bin/env python3
"""Repair native-observed HUD hierarchy/receipt faults through local tiny edits."""
import re
from resume_consolidated_hud import ConsolidatedHud,PATH,ACCEPTED
from resume_relay_source_repairs import RelaySourceRepairs
from resume_three_day_queue import main
from loop_controller.core import Halt,sha
from loop_controller.delivery_policy import HARD_CAP_EPOCH

SOURCE='a64f4bbd5f56b0c15bc105664b04ad60c1a4e283'
ROUND='q0114-fc06e838'
SOURCE_SHA='9b1d94bea95d0a849d130e822caac4e8e968b5ce7e1530a2188b963cb10049c1'
GATE_SHA='7d220e92c6a3129fefab64d7752ee69faec5e1cf12566cff7730ddb1e3ce81e7'
FAILURES=['relay-HUD-outside-captureTextRect','relay-HUD-outside-textRect','relay-objective-hidden',
    'relay-text-missing','chapter-objective-presentation-missing']

def validate_pause(old):
    import json
    expected=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=ROUND,
        task_index=7,task_failures=24,failure_streak=1,diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,
        blocker='Halt: Consolidated HUD positive needs measured diagnosis: '+json.dumps(FAILURES))
    if any(old.get(k)!=v for k,v in expected.items()) or old.get('hud_live_objective_repair_attempted'):
        raise Halt('Require exact native HUD lookup failure and preserved history')

class HudLiveObjective(ConsolidatedHud):
    def validate_recovery(self,old):
        validate_pause(old)
        if sha((self.project/PATH).read_bytes())!=SOURCE_SHA:raise Halt('Local HUD source changed')
        p=self.store.root/'evidence'/(ROUND+'-positive')/'consolidated-hud-gate.json'
        if sha(p.read_bytes())!=GATE_SHA:raise Halt('Original native HUD rejection changed')

    def recovery_settings(self):
        return dict(hud_live_objective_repair_attempted=True,recovery_route='local-native-hud-lookup-repair',
            recovery_change='Read RelaySequence.Objective; correct truthful receipt footers; reacquire late-installed HudStatus. Preserve mechanics and native rejection; require actual active relay objective text in the rendered primary panel.')

    def patch(self,*args,**kwargs):return RelaySourceRepairs.patch(self,*args,**kwargs)

    def source(self,ident):
        raw=(self.project/PATH).read_text();lines=raw.splitlines(True)
        i=next(i for i,line in enumerate(lines) if 'var rt = _relay.GetComponentInChildren<TextMesh>(true);' in line)
        selected=''.join(lines[i:i+2])
        self.patch(ident,'actual-relay-objective',PATH,selected,
            'Native playthrough confirms the objective disappears while relay Active. Actual hierarchy: '
            'RelaySequence is a stationary host with no TextMesh children. RelaySequence.Hud.cs creates RelayHud '
            'under cam.transform and Text under RelayHud. Its UpdateHud ends relayHud.text = s; Objective = s; '
            'and runs before your LateUpdate31000. Replace these two lookup lines with exactly one read: '
            'string two = _relay.Objective ?? "OBJECTIVE UNAVAILABLE"; No state writes or gameplay edits.',
            lambda content,old:re.sub(r'\s+','',content)=='stringtwo=_relay.Objective??"OBJECTIVEUNAVAILABLE";',2)
        raw=(self.project/PATH).read_text();line=next(s for s in raw.splitlines(True) if 'string foot = _relay.AllComplete' in s)
        self.patch(ident,'relay-completed-receipts',PATH,line,
            'This branch is entered only when relay.Active; actual courier and dead-drop are already complete '
            'then. The relay Objective already contains its own progress/ending/failure. Replace only this line '
            'with string foot = "\\nDelivery complete / Dead-drop complete"; so truthful prior receipts stay visible.',
            lambda content,old:re.sub(r'\s+','',content)=='stringfoot="\\nDeliverycomplete/Dead-dropcomplete";',2)
        raw=(self.project/PATH).read_text();line=next(s for s in raw.splitlines(True) if 'string foot = _route.RouteStage' in s)
        self.patch(ident,'chapter-completed-receipt',PATH,line,
            'Actual RouteStage is0/1/2, so >=3 never renders the receipt. This branch already requires RouteStage>=1, '
            'which follows real courier completion. Replace only this line with string foot = "\\nDELIVERY COMPLETE";',
            lambda content,old:re.sub(r'\s+','',content)=='stringfoot="\\nDELIVERYCOMPLETE";',2)
        raw=(self.project/PATH).read_text();line=next(s for s in raw.splitlines(True) if 'if (_hudStatus) _hudStatus.localPosition' in s)
        expected='if (!_hudStatus) { var hs = GameObject.Find("HudStatus"); if (hs) _hudStatus = hs.transform; }'
        self.patch(ident,'late-installed-health-panel',PATH,line,
            'Actual Bootstrap installs MissionDirectorHud at line97 and HudStatus at99. Setup therefore caches null; '
            'native initial/carrying frames show health card overlap. Before this existing positioning line, add '
            'exactly: if (!_hudStatus) { var hs = GameObject.Find("HudStatus"); if (hs) _hudStatus = hs.transform; } '
            'Preserve the existing positioning line byte-for-byte apart from whitespace. No health/text/state changes.',
            lambda content,old:re.sub(r'\s+','',content)==re.sub(r'\s+','',expected+old),3)
        return self.store.get('source_checkpoint')

if __name__=='__main__':raise SystemExit(main(HudLiveObjective))
