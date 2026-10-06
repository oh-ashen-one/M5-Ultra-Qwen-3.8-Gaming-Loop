import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from loop_controller.relay_contract import ANCHORS,inspect_relay,scenarios
from loop_controller.core import Halt
from resume_ordered_relay import validate_module,validate_pause,SOURCE,ACCEPTED,ROUND,HARD_CAP_EPOCH

def row(t,count=0,active=False,failed=False,wrong=0,index=0,keys=(),restart=0):
    sites=[]
    for i,a in enumerate(ANCHORS):
        center=[a[0],.6,a[2]];size=[.9,.8,.6]
        sites.append(dict(index=i,exists=True,active=active,actorChild=False,position=a.copy(),
            originalMeshReuse=True,rendererCount=int(active),boundsCenter=center,boundsSize=size,
            colliderCount=int(active),colliderCenter=center.copy(),colliderSize=size.copy()))
    text='RELAY '+('COMPLETE' if count==3 else 'FAILED' if failed else 'NEXT')
    hud=dict(visible=active,text=text,**{k:[.52,.07,.91,.2] for k in ['textRect','cardRect','captureTextRect','captureCardRect']})
    return dict(time=t,keys=list(keys),restarts=restart,player=[ANCHORS[index][0],.195,ANCHORS[index][2]-1],
        mode='foot',mission='complete',routeChapter=dict(complete=active,stage=2 if active else 0),
        relay=dict(present=True,valid=True,componentCount=1,count=count,expected=count,active=active,
            complete=count==3,failed=failed,wrongOrders=wrong,sites=sites,hud=hud,objective=text,remaining=max(0,77.6-t)))

def positive():
    return [row(1),row(32.6,active=True),row(37,active=True,keys=('F',)),
        row(38.45,active=True),row(38.6,1,True,keys=('F',)),row(40,1,True),
        row(49.1,2,True,index=1,keys=('F',)),row(51,2,True),
        row(59.7,3,True,index=2,keys=('F',)),row(60,3,True),row(61.1,keys=('R',),restart=1),row(63,restart=1)]

def red():
    return [row(1),row(32.6,active=True),row(38.6,1,True,keys=('F',)),row(40,1,True),
        row(49.9,0,True,wrong=1,index=2,keys=('F',)),row(50.5,0,True,wrong=1,index=2,keys=('F',)),
        row(76,0,True,wrong=1,index=2),row(77.7,0,True,failed=True,wrong=1,index=2),
        row(78.3,0,True,failed=True,wrong=1,index=2,keys=('F',)),row(79.1,keys=('R',),restart=1),row(81,restart=1)]

class RelayTests(unittest.TestCase):
    def test_real_ordered_foot_interactions_and_reset_are_required(self):
        self.assertTrue(inspect_relay(positive(),'positive')['passed'])
        for kind in ('remote','vehicle','no-F','held-F','wrong-anchor','missing-collider','floating','hidden-HUD','legacy-write','bad-reset'):
            r=positive()
            if kind=='remote':r[4]['player']=[50,.135,18]
            if kind=='vehicle':r[4]['mode']='vehicle'
            if kind=='no-F':r[4]['keys']=[]
            if kind=='held-F':r[3]['keys']=['F']
            if kind=='wrong-anchor':r[4]['relay']['sites'][0]['position'][0]+=3
            if kind=='missing-collider':r[4]['relay']['sites'][0]['colliderCount']=0
            if kind=='floating':r[4]['relay']['sites'][0]['boundsCenter'][1]+=.2
            if kind=='hidden-HUD':r[4]['relay']['hud']['visible']=False
            if kind=='legacy-write':r[4]['mission']='failed'
            if kind=='bad-reset':r[10]['relay']=copy.deepcopy(r[9]['relay']);r[11]['relay']=copy.deepcopy(r[9]['relay'])
            with self.subTest(kind=kind):self.assertFalse(inspect_relay(r,'positive')['passed'])

    def test_wrong_order_timeout_and_latched_failure_cannot_fake_success(self):
        self.assertTrue(inspect_relay(red(),'wrong-timeout')['passed'])
        for kind in ('early-timeout','wrong-order-no-edge','wrong-order-remote','repeat-held','advance-after-failed'):
            r=red()
            if kind=='early-timeout':r[7]['time']=60
            if kind=='wrong-order-no-edge':r[4]['keys']=[]
            if kind=='wrong-order-remote':r[4]['player']=[50,.135,18]
            if kind=='repeat-held':r[5]['relay']['wrongOrders']=2
            if kind=='advance-after-failed':r[8]['relay']['count']=r[8]['relay']['expected']=1
            with self.subTest(kind=kind):self.assertFalse(inspect_relay(r,'wrong-timeout')['passed'])
        self.assertFalse(inspect_relay(red(),'positive')['passed'])
        self.assertFalse(inspect_relay(positive(),'wrong-timeout')['passed'])

    def test_inactive_case_and_missing_observer_are_independent_red_checks(self):
        rows=[row(1),row(5),row(6,keys=('F',))]
        self.assertTrue(inspect_relay(rows,'inactive')['passed'])
        rows[-1]=row(6,active=True)
        self.assertFalse(inspect_relay(rows,'inactive')['passed'])
        self.assertFalse(inspect_relay([{'time':1}],'inactive')['passed'])

    def test_replays_preserve_proven_chapter_and_add_only_ordinary_input(self):
        original=dict(duration=53,steps=[dict(start=4,end=5,keys=['W']),dict(start=32.5,end=32.8,keys=['F']),dict(start=50,end=50.3,keys=['R'])],captures=[3,32.55,50.6,52])
        saved=copy.deepcopy(original);probes=scenarios(original)
        self.assertEqual(original,saved)
        for name in ('positive','wrong-timeout'):
            self.assertEqual(probes[name]['steps'][:2],original['steps'][:2])
            self.assertTrue(all(set(s)=={'start','end','keys'} for s in probes[name]['steps']))
        self.assertEqual(probes['positive']['duration'],64)
        self.assertEqual(probes['wrong-timeout']['duration'],82)

    def test_recovery_keeps_exact_baseline_and_does_not_overwrite_prior_work(self):
        s=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=ROUND,
            task_index=7,task_failures=24,failure_streak=1,diagnosis_used=True,second_street_attempts=4,
            overall_deadline_epoch=HARD_CAP_EPOCH,ground_cited_review_recovered=True,
            blocker='Halt: Ground scope and corrected next gameplay design saved; seal additive mission acceptance before implementation',
            street_ground_outcome={'accepted':True},revised_pacing_plan={'ok':True})
        validate_pause(s)
        for field,value in [('task_failures',0),('overall_deadline_epoch',HARD_CAP_EPOCH+1),('ordered_relay_attempted',True)]:
            with self.assertRaises(Halt):validate_pause({**s,field:value})
        for content in ['LoopSignals.Mission="failed";','CreatePrimitive','LoopRuntime','BootstrapInstall']:
            with self.assertRaises(ValueError):validate_module(content)

if __name__=='__main__':unittest.main()
