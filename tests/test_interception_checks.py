import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from loop_controller.interception_checks import inspect_interception,NAMES,probes
from loop_controller.consolidated_hud import inspect_hud
from test_consolidated_hud import row as hud_row


class InterceptionTests(unittest.TestCase):
    def evidence(self,case='positive'):
        events=[]
        if case=='positive':
            for i,name in enumerate(sorted(NAMES)):
                for j in range(3):
                    t=7.6+i+j*.2
                    events.append(dict(time=t,restarts=0,keys=['Mouse0'],shotsBefore=len(events),shotsAfter=len(events)+1,
                        hitsBefore=len(events),hitsAfter=len(events)+1,targets=[dict(name=name,hpBefore=3-j,hpAfter=2-j,
                        colliderRayHit=True,visualBoundsRayHit=True,viewportContainsCenter=True,firstRayTarget=True)]))
        rows=[]
        for index in range(1,191):
            t=index*.1; active=5<=t<15 and case!='inactive'; reset=t>=15 and case!='inactive'
            targets=[]; stopped=0; escaped=int(active and case=='escape' and t>=11)
            for i,name in enumerate(sorted(NAMES)) if active else []:
                hp=3-sum(e['time']<=t+1e-6 and e['targets'][0]['name']==name for e in events)
                alive=hp>0;stopped+=int(not alive);out=bool(escaped and i==0)
                targets.append(dict(name=name,hp=hp,alive=alive,renderers=22 if alive and not out else 0,
                    colliderEnabled=alive and not out,dynamicBody=True,gravity=True,
                    position=[58 if out else 24+1.6*(t-5),.14,22-i*4],footGap=0,groundCollider='StreetPavement'))
            complete=active and stopped==3
            objective=f'INTERCEPT RUNNERS {stopped}/3\nMove to aim; Mouse0 fire\nStopped {stopped} / Escaped {escaped}\nRelay complete | R reset'
            state=dict(present=True,valid=True,componentCount=1,active=active,complete=complete,failed=bool(escaped),
                stopped=stopped,escaped=escaped,spawned=len(targets),targets=targets,objective=objective if active else '')
            rivals=copy.deepcopy(targets)+[dict(name='Rival',hp=3,alive=True,renderers=22,colliderEnabled=True)]
            rows.append(dict(time=t,restarts=int(reset),keys=['R'] if reset and t<15.3 else [],health=44,
                mission='complete' if active else 'active',relay=dict(complete=active),
                routeChapter=dict(complete=active,hudPanels=[dict(name='MissionBoard',text=objective)]),
                interception=state,rivals=rivals))
        return rows,events

    def test_real_hits_movement_isolation_ending_and_reset(self):
        rows,events=self.evidence();result=inspect_interception(rows,events,'positive')
        self.assertTrue(result['passed'],result['failure']);self.assertTrue(result['secondary_target_isolation_qualified'])
        self.assertEqual(len(result['actual_new_target_damage']),9)
        self.assertFalse(result['final_game_accepted'])

    def test_false_kill_teleport_collider_damage_and_reset_fail(self):
        for defect in ['off-aim','multiple-hit','collateral-hide','false-stop','floating','kinematic','no-reset','rearm']:
            rows,events=self.evidence()
            if defect=='off-aim': events[0]['targets'][0]['firstRayTarget']=False
            if defect=='multiple-hit': events[0]['targets'].append(dict(name='Rival',hpBefore=3,hpAfter=2))
            if defect=='collateral-hide':
                for r in rows:
                    if 8<=r['time']<=8.25: r['rivals'][-1]['renderers']=0
            if defect=='false-stop': next(r for r in rows if r['time']>=5)['interception']['stopped']=1
            if defect in ('floating','kinematic'):
                for r in rows:
                    if r['interception']['targets']:
                        r['interception']['targets'][0]['footGap']=1 if defect=='floating' else 0
                        r['interception']['targets'][0]['dynamicBody']=defect!='kinematic'
            if defect=='no-reset': rows=[r for r in rows if r['time']<15]
            if defect=='rearm': rows[-1]['interception']['active']=True
            with self.subTest(defect=defect):self.assertFalse(inspect_interception(rows,events,'positive')['passed'])

    def test_escape_is_a_living_boundary_crossing_not_a_kill(self):
        rows,events=self.evidence('escape'); result=inspect_interception(rows,events,'escape')
        self.assertTrue(result['passed'],result['failure'])
        for r in rows:
            if r['interception']['escaped']:r['interception']['targets'][0]['position'][0]=40
        self.assertIn('escape-not-a-real-live-boundary-crossing',inspect_interception(rows,events,'escape')['failure'])
        rows,events=self.evidence('inactive')
        self.assertTrue(inspect_interception(rows,events,'inactive')['passed'])

    def test_new_hud_phase_still_requires_truthful_counts_and_actual_objective(self):
        row=hud_row(70,'relay-complete');text='INTERCEPT RUNNERS 1/3\nMove to aim; Mouse0 fire\nStopped 1 / Escaped 0\nRelay complete | R reset'
        row['interception']=dict(active=True,valid=True,complete=False,failed=False,stopped=1,escaped=0,objective=text)
        row['routeChapter']['hudPanels'][0]['text']=text
        # Four lines need the same real minimum line height as prior phases.
        row['routeChapter']['hudPanels'][0]['textRect'][1]=.78
        row['routeChapter']['hudPanels'][0]['captureTextRect'][1]=.78
        self.assertTrue(inspect_hud([row])['passed'])
        row['interception']['stopped']=2
        self.assertIn('interception-actual-counts-not-rendered',inspect_hud([row])['failure'])


if __name__=='__main__':unittest.main()
