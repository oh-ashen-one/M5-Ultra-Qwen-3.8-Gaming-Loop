#!/usr/bin/env python3
"""Preserve exhausted whole-module role; locally author three bounded partials."""
import json
import re
from resume_ordered_relay import OrderedRelay,SOURCE,ACCEPTED,PLAN_SHA,BOOT
from resume_three_day_queue import main
from continue_game_queue import ReadBoundEdits
from loop_controller.core import Files,Halt,read_json,sha,verify_seal
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.model import tool
from resume_ground_cited_review import HASHES as GROUND_HASHES,ROUND as GROUND_ROUND

ROUND='q0109-243da542'
RESPONSE_SHA='d76d84710eb25f33c4667f1bc15ac708575a154021555b6fa429bde83b685960'
PARTS=['Assets/Game/RelaySequence.cs','Assets/Game/RelaySequence.Props.cs','Assets/Game/RelaySequence.Hud.cs']

def validate_pause(old):
    expected=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=ROUND,
        task_index=7,task_failures=24,failure_streak=1,diagnosis_used=True,second_street_attempts=4,
        overall_deadline_epoch=HARD_CAP_EPOCH,ordered_relay_attempted=True,
        blocker='Halt: Local relay component was not saved')
    if any(old.get(k)!=v for k,v in expected.items()) or old.get('relay_microtasks_attempted'):
        raise Halt('Require exact exhausted relay role and unchanged game/history')

def validate_part(content,part):
    if not isinstance(content,str) or len(content.splitlines())>150 or len(content.encode())>12000:
        raise ValueError('Save one bounded partial, at most150lines/12KB')
    for term in ('LoopRuntime','LoopRelayObservation','LoopRouteObservation','LoopInput.Replay','GetCommandLineArgs',
        'System.IO','UnityEditor','CreatePrimitive','class LoopSignals','BootstrapInstall'):
        if term in content:raise ValueError('Only actual additive gameplay APIs: '+term)
    if re.search(r'LoopSignals\.\w+\s*(?:=(?!=)|\+\+|--|[+*/-]=)',content):raise ValueError('Legacy signals are read-only')
    if 'partial class RelaySequence' not in content:raise ValueError('Use the one agreed partial component')
    required=[['Install(GameObject player, Camera cam)','ActivationCount','ExpectedIndex','WrongOrderCount','Remaining','Relays'],
        ['BuildProps(','PaintSites(','SetSitesVisible('],['BuildHud(','UpdateHud(','HideHud(','RelayHud']][part]
    if any(x not in content for x in required):raise ValueError('Missing agreed partial API')
    return content

class RelayMicrotasks(OrderedRelay):
    def validate_recovery(self,old):
        validate_pause(old);self.verify_presentation()
        e=self.store.root/'evidence'/GROUND_ROUND
        for name,digest in GROUND_HASHES.items():
            if sha((e/name).read_bytes())!=digest:raise Halt('Preserve ground evidence')
        verify_seal(e/'captures',GROUND_HASHES['captures/manifest.json'])
        if sha((self.store.root/'evidence/q0108-0480baca/revised-pacing-plan.json').read_bytes())!=PLAN_SHA:
            raise Halt('Saved local proposal changed')
        raw=(self.store.root/'private/sessions'/(ROUND+'-relay-module')/'response-000.json').read_bytes()
        if sha(raw)!=RESPONSE_SHA or json.loads(raw)['choices'][0].get('finish_reason')!='length':
            raise Halt('Preserve the actual exhausted response')
        if any((self.project/p).exists() for p in PARTS):raise Halt('Never overwrite an existing relay partial')

    def recovery_settings(self):
        return dict(relay_microtasks_attempted=True,recovery_route='three-local-relay-partials',
            recovery_change='Preserve10000-token exhausted no-tool response; separate local state logic, original-mesh prop fitting and HUD into small shared-API roles; unchanged external acceptance.')

    def source(self,ident):
        files=Files(self.project,self.store);edits=ReadBoundEdits(files);raw=(self.project/BOOT).read_text()
        core=('Create ONLY the gameplay state partial, no mesh/HUD method implementations. Namespace ChicagoGame; '
            'public partial class RelaySequence : MonoBehaviour. Static exact Install(GameObject player, Camera cam), '
            'create one host named RelaySequence, store private GameObject player and Camera cam, obtain RouteMission '
            'from GameObject.Find("RouteMission").GetComponent<RouteMission>(), store lastRestarts from LoopSignals.Restarts. '
            'Call BuildProps(),BuildHud(),SetSitesVisible(false),HideHud(); these methods are supplied by later partials. '
            'Public bool Active,AllComplete,Failed; public int ActivationCount,ExpectedIndex,WrongOrderCount; public '
            'float Remaining; public string Objective; public Transform[] Relays initialized length3. Private float '
            'armedAt,flashUntil; private int flashIndex=-1. Actual chapter public RouteStage0/1/2 and RouteComplete. '
            'Update FIRST detects Restarts change: clear all public state,flash, hide props/HUD, return immediately. '
            'When inactive, arm only when chapter.RouteStage==2 && chapter.RouteComplete; setActive true, armedAt=Time.time, '
            'Remaining45, show sites, return. Active stays true after completion/failure until globalR. Each active update '
            'before outcome sets Remaining=max(0,45-elapsed); at45 setFailed=true, no future progress. Only fresh '
            'LoopInput.Pressed(KeyCode.F), Mode=="foot", Active && !AllComplete && !Failed interacts. Match actual player '
            'XZ distance<=1.5m to one Relays root. Expected index increments count/expected together; at3AllComplete. '
            'Wrong index sets both0, increments WrongOrderCount once, flashIndex=that index,flashUntil=Time.time+.3; '
            'does NOT restart clock. Far or held F does nothing. Never write LoopSignals or chapter fields. '
            'LateUpdate calls PaintSites(Time.time<flashUntil?flashIndex:-1) and UpdateHud(); HUD partial owns Objective '
            'text and can read the public fields/player. Helper calls are instance private methods shared by partials. '
            'Avoid redundant state copies. Source only, target<100lines. Call create_part now.')
        props=('Create ONLY the original-mesh prop partial of namespace ChicagoGame public partial class RelaySequence '
            '(no base class needed). Existing core below is authoritative. Implement private instance void BuildProps(), '
            'void SetSitesVisible(bool value), void PaintSites(int flash). Do not duplicate core fields/methods. '
            'Build three stationary identity roots named RelaySite1/2/3 at(53,.2,27),(41,.2,9),(29,.2,27), store them '
            'in existing Relays array. Reuse GameObject.Find("AlleyDumpster") fallback dumpster_a original mesh hierarchy. '
            'Clone ONLY that prop into each root, preserve its original world mesh orientation and scale, then uniform '
            'scale cloned child until aggregate MeshRenderer bounds maxdimension1.0m. Bounds start from first real '
            'MeshRenderer; recalculate after scale, shift clone so aggregate centerXZ equals rootXZ and minY equals '
            'root.y=.2 (already worldheight, no second offset). Original sharedMesh assets remain shared. Disable all '
            'colliders ONLY on each clone; add exactly one root BoxCollider whose localcenter and size match final '
            'aggregate render bounds, root unit/identity. No primitive creation or original edits. Copy each material; '
            'muted charcoal body with next site teal, activated site green; flash index red. Emission off or restrained '
            'accent, no neon cube. PaintSites uses Active/ActivationCount/ExpectedIndex/AllComplete/Failed plus flash; '
            'failed sites muted red, initial/cleared sites charcoal. Keep own per-site Renderer arrays for coloring; '
            'SetSitesVisible only toggles own roots. Add small labels1/2/3 using TextMesh and LegacyRuntime.ttf, '
            'face the camera via PaintSites using existing cam field. Add labels AFTER fitting/collider, never include '
            'their generated text in the mesh geometry fit. No Update/LateUpdate methods; core calls you. Target<110lines. '
            'Call create_part now.\nACTUAL CORE:\n')
        hud=('Create ONLY HUD partial namespace ChicagoGame public partial class RelaySequence. Existing core/props '
            'are authoritative. Implement private void BuildHud(),void UpdateHud(),void HideHud(); no Update/LateUpdate '
            'method and no duplicate fields from prior parts. Own TextMesh relayHud and Transform relayCard. Build '
            'GameObject RelayHud as existing cam child, localposition(.52,-.55,1.6),identityrotation. TextMesh font '
            'LegacyRuntime.ttf,size40,characterSize.0125,UpperCenter/Center,mutedcyan, initiallyempty. Copy existing '
            'RouteHud/HudCard child (fallback any original HudCard) into RelayHud, localposition(0,-.065,.025), '
            'localscale(1.3,.23,.01),identityrotation, disable ONLY clone collider. No primitives or other HUD edits. '
            'HideHud empties text and hides cloned card, Objective empty. UpdateHud when !Active calls HideHud; '
            'otherwise show card and compact readable TWO lines <=34characters each: RELAY count/3 plus Remaining '
            'seconds; next numbered NORTH/SOUTH/NORTHWEST site and horizontal distance + F. Use actual player and '
            'Relays positions. On AllComplete text RELAY COMPLETE / Three relays online; on Failed RELAY FAILED / '
            'R to retry. Update public Objective with displayed text; no change to health/mission signals or other '
            'panels/camera. Do not expose coordinates or implementation jargon in HUD. Target<70lines. '
            'Call create_part now.\nACTUAL PARTIALS:\n')
        for i,(path,prompt,budget) in enumerate(zip(PARTS,[core,props,hud],[6144,6144,4096])):
            self.c.update(output_tokens=budget,model_timeout_seconds=330)
            self.store.set(stage='local-relay-'+['state','props','hud'][i]);self.store.report()
            if i:prompt+='\n\n'.join((self.project/p).read_text() for p in PARTS[:i])
            def create(action,f,index=i,target=path):
                return edits.create(action,dict(path=target,content=validate_part(f['content'],index)))
            self.model.session('builder',ident+'-relay-part-'+str(i),
                'You are local Qwen, sole game author. Complete this ONE small partial using create_part. No prose, '
                'markdown or alternative drafts; required next output is the tool call.',
                prompt,[tool('create_part','Save only the complete currently requested gameplay partial.',{'content':{'type':'string'}})],
                {'create_part':create},turns=1,reasoning_effort='low')
            if not (self.project/path).exists():raise Halt('Local relay partial not saved: '+path)
            candidate=self.checkpoint_source('Local Qwen: relay '+['state logic','original-mesh props','objective HUD'][i])
            self.store.set(source_checkpoint=candidate,candidate_commit=candidate);self.store.report()
        return self.install(ident,raw)

if __name__=='__main__':raise SystemExit(main(RelayMicrotasks))
