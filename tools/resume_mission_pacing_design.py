#!/usr/bin/env python3
"""Preserve the street FIX and obtain a bounded local mission design on the same queue."""
import json
from resume_saved_door import SavedDoor, ACCEPTED
from resume_three_day_queue import main
from loop_controller.core import Halt, atomic, sha, verify_seal
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.model import tool

SOURCE='9522003c685cf9e74afdcc45bae94368baa04e7e'
ROUND='q0092-5a49246f'
HASHES={
    'scoped-gate.json':'d19b59bedce92cf1cdb8ddc5536be5e20de8d3d0e32b2f1f2109dad36adf2c0d',
    'critic.json':'9e95ccc970dd2e9ada3dbe39f25aab642c205c2ad607630f66e7cfeb9ced1c94',
    'captures/manifest.json':'522e5e1f5e697139196342e6975b5b8d37d693d9debdb3e43ab912c804f2f8ab',
}
REQUIRED={'walk','world','motor','courier','failure-retry','combat-foot','combat-wall',
          'combat-driving','aim-miss','aim-near-cover'}
FIELDS=('decision','first_objective','legacy_compatibility','state_and_observation',
        'normal_input_proof','pacing_path','first_source_scope')

def validate_pause(old):
    expected=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=ROUND,
        task_index=7,task_failures=24,failure_streak=1,diagnosis_used=True,second_street_attempts=4,
        overall_deadline_epoch=HARD_CAP_EPOCH,camera_overlap_micro_attempted=True,
        blocker='Halt: Cause-based camera/street correction did not qualify; preserve measured failure')
    if any(old.get(k)!=v for k,v in expected.items()) or old.get('mission_pacing_design_attempted'):
        raise Halt('Expected exact preserved street visual FIX before distinct mission design')

def validate_native_outcome(gate,review,manifest):
    checks=gate.get('regressions',{}).get('regressions',[])
    if (not gate.get('passed') or gate.get('candidate_commit')!=SOURCE
            or manifest.get('candidate')!=SOURCE or manifest.get('scope')!='connected-map-extension'
            or len(checks)!=10 or {x.get('test') for x in checks}!=REQUIRED
            or not all(x['gate'].get('passed') and x['gate'].get('candidate_commit')==SOURCE for x in checks)
            or gate.get('return_camera_review',{}).get('verdict')!='PASS'
            or not review.get('ok') or review.get('verdict')!='FIX'):
        raise Halt('Require scoped camera/native PASS and unchanged broader visual FIX; never promote the street')
    return review

def evidence(bundle):
    for name,digest in HASHES.items():
        if sha((bundle/name).read_bytes())!=digest:raise Halt('Original street evidence changed: '+name)
    manifest=verify_seal(bundle/'captures',HASHES['captures/manifest.json'])
    return validate_native_outcome(json.loads((bundle/'scoped-gate.json').read_text()),
        json.loads((bundle/'critic.json').read_text()),manifest)

def submitted_plan(_,fields):
    if set(fields)!=set(FIELDS) or any(not isinstance(v,str) or not 20<=len(v)<=2400 for v in fields.values()):
        raise ValueError('Return every concise operational design field, each20..2400characters')
    return dict(ok=True,**fields)

class MissionPacingDesign(SavedDoor):
    def validate_recovery(self,old):
        validate_pause(old);evidence(self.store.root/'evidence'/ROUND);self.accepted_probe()

    def recovery_settings(self):
        return dict(mission_pacing_design_attempted=True,second_street_accepted=False,
            recovery_route='independent-connected-mission-design-with-preserved-street-fix',
            recovery_change='Preserve all ten native passes, focused camera PASS, broad visual FIX, counters and checkpoint; define the next local mission scope')

    def work(self):
        review=evidence(self.store.root/'evidence'/ROUND)
        finding=dict(round=ROUND,candidate=SOURCE,scope='Second street presentation and route readability',
            verdict='FIX',summary=review['summary'],fixes=review['fixes'],native_regressions_passed=True,
            accepted=False,disposition='Preserved while the distinct mission scope is designed; not a waiver of final visual gates')
        findings=self.store.get('deferred_visual_findings',[])+[finding]
        task=dict(phase='mission',outcome='Define a real connected objective after the existing courier component, with separate full-route acceptance')
        ident=self.begin(task,'local-connected-mission-design')
        self.store.set(deferred_visual_findings=findings,next_task='Seal additive mission acceptance, then local-Qwen source and native proof')
        self.store.event('street-visual-fix-preserved-mission-design',**finding,
            last_playable_checkpoint_unchanged=ACCEPTED,original_counters_preserved=True)
        paths=['Assets/Game/Mission.cs','Assets/Game/VehicleInteraction.cs','Assets/Game/HudStatus.cs',
               'Assets/Game/Combat.cs','Assets/Game/ConnectedStreet.cs']
        sources='\n\n'.join(p+'\n'+(self.project/p).read_text() for p in paths if (self.project/p).exists())
        boot=(self.project/'Assets/Game/Bootstrap.cs').read_text()
        sources+='\nBOOTSTRAP BEFORE CAMERA:\n'+boot.split('    public class Follow')[0]
        self.c.update(output_tokens=8192,model_timeout_seconds=400)
        self.store.report()
        plan=self.model.session('planner',ident+'-connected-mission-design',
            'You are local Qwen, the game designer and substantive game author. Return a compact implementable decision, not private reasoning or source code.',
            'The broader street critic is FIX and remains so, although all10current-source mechanics regressions and '
            'the focused return-angle comparison pass. Stop spending the next scope on camera microframing. The owner needs '
            'a connected, approximately10minute native Chicago mission. The current CourierMission has a30second '
            'deadline from spawn and short delivery ending; traversal takes longer. The generic polish editor intentionally '
            'protects Mission.cs and VehicleInteraction.cs, so a dedicated mission scope is required. Do not just increase '
            'the deadline, relabel short delivery as the whole game, weaken old tests, pad with waiting, or add test-only behavior. '
            'Recommend one small meaningful follow-on objective using the already physically traversable alley and east street. '
            'A possible architecture is a distinct connected-route component that treats the existing courier delivery as '
            'a first chapter; its overall progress/ending must be separately observed and must not reinterpret the legacy '
            'courier complete signal. You own the design choice. Preserve the legacy pickup/delivery anchors,30second '
            'challenge/failure/retry proof, controls, collisions, camera and combat in the first source scope. If incompatible, '
            'state the actual conflict and propose a legitimate player-facing transition with additive acceptance, never '
            'a hidden harness branch. No installs or new art volume. Reuse original rendered meshes for world markers. '
            'Return a first milestone that can be proved in<=180seconds: concrete world locations, real proximity/input, '
            'on-foot/driving state transitions, fixed world anchors, clear objective/feedback, and R reset. This short '
            'milestone is explicitly NOT ten-minute acceptance. Then explain a credible path toward varied connected '
            'gameplay ending around540..660seconds without timer locks or repeated idle loops. Current playable topology '
            'is coreX-1..6/Z-2..30, alleyX6..22/Z8..20 and provisional east streetX22..60/Z8..28; newer street presentation '
            'is unaccepted. Normal controlsWASD/E/F/R/Mouse0; do not inspect replay/fixture/scenario metadata. '
            'Specify the smallest first source file/span, proposed externally observable real objects/state, normal-input '
            'positive proof and red cases (no input, remote F, wrong actor/mode, stale carry/reset, early ending). '
            'Keep each returned field short and call submit_plan now; no source edits or giant task list. '
            '\nPRESERVED VISUAL FINDINGS:\n'+json.dumps(finding)+'\nEXACT CURRENT SOURCE:\n'+sources,
            [tool('submit_plan','Save concise connected-mission design and its next externally testable increment.',
                {name:{'type':'string'} for name in FIELDS})],{'submit_plan':submitted_plan},
            turns=1,reasoning_effort='low')
        bundle=self.store.root/'evidence'/ident;bundle.mkdir(exist_ok=True)
        atomic(bundle/'connected-mission-plan.json',plan)
        if not plan.get('ok'):raise Halt('Connected mission planner supplied no complete decision; preserve evidence and source')
        self.store.set(connected_mission_plan=plan,connected_mission_plan_evidence=str(bundle.relative_to(self.store.root)),
            stage='connected-mission-design-saved',next_task='Seal additive mission acceptance, then local-Qwen implementation',
            feedback={'preserved_visual_fix':finding},task_design='')
        self.store.event('local-connected-mission-plan-saved',round=ident,source_unchanged=SOURCE,
            accepted_checkpoint_unchanged=ACCEPTED,game_implemented=False,final_game_accepted=False)
        self.store.report()
        raise Halt('Connected mission design saved; dedicated external acceptance and local source implementation are next')

if __name__=='__main__':raise SystemExit(main(MissionPacingDesign))

