import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from loop_controller.consolidated_hud import inspect_hud

def row(t,state='grab',restart=0):
    texts={'grab':'COURIER: grab parcel\n3m F grab / E enter coupe\nWASD move / R reset',
        'carrying':'PARCEL IN HAND\nGreen pad 20m / F deliver',
        'courier-failed':'MISSION FAILED\nR to retry',
        'dead-drop':'EAST DEAD-DROP\nDrive 20m / E exit\nDELIVERY COMPLETE',
        'relay':'RELAY 1/3 30s\n2 SOUTH 18m F\nDelivery complete / Dead-drop complete',
        'relay-complete':'RELAY COMPLETE\nThree relays online / R reset\nDelivery complete / Dead-drop complete',
        'relay-failed':'RELAY FAILED\nR to retry\nDelivery complete / Dead-drop complete'}
    def panel(name,text,tr,cr):return dict(name=name,text=text,visible=True,visibleRenderers=2,
        textRect=tr,cardRect=cr,captureTextRect=tr.copy(),captureCardRect=cr.copy())
    panels=[panel('MissionBoard',texts[state],[.44,.78,.93,.90],[.41,.76,.96,.93]),
        panel('HudStatus','HEALTH 60\nWANTED . . .',[.06,.85,.2,.9],[.04,.83,.38,.93])]
    panels += [dict(name=n,visible=False,visibleRenderers=0,text='old actual source text') for n in ['MissionHud','RouteHud','RelayHud']]
    chapter=state in ['dead-drop','relay','relay-complete','relay-failed'];relay=state.startswith('relay')
    return dict(time=t,restarts=restart,mission='complete' if chapter else ('failed' if state=='courier-failed' else 'active'),
        missionObjects=[dict(name='Parcel',playerChild=state=='carrying')],
        routeChapter=dict(stage=2 if relay else int(chapter),hudPanels=panels,liveAspect=4/3,captureAspect=16/9,
            cacheBoundsCenter=[50,.874,18],cacheBoundsSize=[2.534,1.468,1.346],emissiveRenderers=1),
        relay=dict(active=relay,complete=state=='relay-complete',failed=state=='relay-failed',count=1))

class ConsolidatedHudTests(unittest.TestCase):
    def test_source_tool_preserves_state_and_harness_boundaries(self):
        from resume_consolidated_hud import validate_module
        source='using UnityEngine; [DefaultExecutionOrder(31000)] class MissionDirectorHud { }\n// Install(GameObject player, Camera cam) MissionBoard MissionHud RouteHud RelayHud HudStatus'
        validate_module(source)
        for bad in ['LoopSignals.Mission="complete";','LoopSignals.Restarts++;','LoopRuntime.CaptureWidth',
                    'GameObject.CreatePrimitive(', 'System.IO.File.ReadAllText(', 'Destroy(other);']:
            with self.subTest(bad=bad),self.assertRaises(ValueError):validate_module(source+'\n'+bad)

    def test_resume_preserves_the_corrected_plan_boundary_and_cap(self):
        from resume_consolidated_hud import validate_pause,SOURCE,ACCEPTED,ROUND
        from loop_controller.delivery_policy import HARD_CAP_EPOCH
        from loop_controller.core import Halt
        state=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=ROUND,
            task_index=7,task_failures=24,failure_streak=1,diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,
            blocker='Halt: Corrected next gameplay plan saved; continue authorized consolidated HUD implementation')
        validate_pause(state)
        for change in [{'task_failures':0},{'consolidated_hud_attempted':True},{'source_checkpoint':'other'},
                       {'overall_deadline_epoch':HARD_CAP_EPOCH+3600}]:
            with self.subTest(change=change),self.assertRaises(Halt):validate_pause({**state,**change})

    def test_truthful_progress_failure_and_reset_on_two_real_projections(self):
        rows=[row(i+1,s) for i,s in enumerate(['grab','carrying','courier-failed','dead-drop','relay','relay-complete','relay-failed'])]
        rows.append(row(9,'grab',1));result=inspect_hud(rows,['relay','relay-complete','relay-failed'])
        self.assertTrue(result['passed'],result['failure']);self.assertEqual(result['reset_grab_samples'],1)

    def test_hidden_text_does_not_hide_a_competing_card_and_visual_defects_fail(self):
        for defect in ['card','overlap','tiny','clip','capture','backing','receipt','phase','cache','emission']:
            value=row(2,'relay');p=value['routeChapter']['hudPanels'][0]
            if defect=='card':value['routeChapter']['hudPanels'][2]['visibleRenderers']=1
            if defect=='overlap':p['cardRect']=[.1,.76,.65,.93]
            if defect=='tiny':p['textRect']=[.44,.88,.93,.90]
            if defect=='clip':p['captureCardRect'][2]=1.01
            if defect=='capture':del value['routeChapter']['captureAspect']
            if defect=='backing':p['textRect'][0]=.1
            if defect=='receipt':p['text']='RELAY 1/3 30s\n2 SOUTH 18m F'
            if defect=='phase':value['relay']['complete']=True
            if defect=='cache':value['routeChapter']['cacheBoundsCenter'][1]=3
            if defect=='emission':value['routeChapter']['emissiveRenderers']=3
            with self.subTest(defect=defect):self.assertFalse(inspect_hud([value])['passed'])

    def test_reset_cannot_keep_completed_receipts_or_move_primary_anchor(self):
        rows=[row(1,'relay-complete'),row(3,'grab',1)]
        rows[1]['routeChapter']['hudPanels'][0]['text']+='\nDelivery complete'
        self.assertIn('premature-or-stale-receipt',inspect_hud(rows)['failure'])
        rows=[row(1),row(3,'grab',1)];rows[1]['routeChapter']['hudPanels'][0]['textRect'][3]=.91
        self.assertIn('primary-panel-anchor-moves',inspect_hud(rows)['failure'])
        self.assertFalse(inspect_hud([row(1)],['relay-complete'])['passed'])

if __name__=='__main__':unittest.main()
