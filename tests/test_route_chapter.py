import copy
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from loop_controller.route_chapter import inspect_chapter,ANCHOR

def row(t,stage=0,mode='foot',keys=(),restart=0,player=None,vehicle=None):
    return dict(time=t,mode=mode,keys=list(keys),restarts=restart,
        mission='active' if stage==0 else 'complete',
        player=player or [50,.14,18],vehicle=vehicle or [45,0,18],
        visibleText=['EAST DEAD-DROP objective'] if stage else [],
        routeChapter=dict(present=True,valid=True,componentCount=1,stage=stage,complete=stage==2,
            cacheExists=True,cacheActive=stage>0,actorChild=False,originalMeshReuse=True,
            cachePosition=list(ANCHOR),rendererCount=2 if stage else 0,
            objective='East dead-drop' if stage else ''))

def positive():
    return [row(1),row(2,1,'vehicle',('F',),vehicle=[1,0,26]),
        row(3,1,'vehicle',('W',)),row(4,1,'foot',('E',),player=[45,.14,19.5]),
        row(5,2,'foot',('F',)),row(6,0,'foot',('R',),restart=1)]

class RouteChapterTests(unittest.TestCase):
    def test_real_handoff_arrival_exit_close_interaction_and_reset_pass(self):
        result=inspect_chapter(positive())
        self.assertTrue(result['passed'],result)
        self.assertEqual(result['completions'],[5])
        self.assertFalse(result['final_game_accepted'])

    def test_no_input_or_remote_interaction_cannot_replace_actual_completion(self):
        for values in [[row(1),row(5,keys=('F',))],
                       [row(1),row(2,1,'vehicle'),row(3,1,'foot',('F',),player=[1,.14,1])]]:
            self.assertFalse(inspect_chapter(values)['passed'])
        self.assertTrue(inspect_chapter([row(1),row(5,keys=('F',))],expect_inactive=True)['passed'])

    def test_wrong_mode_distance_stale_input_missing_arrival_or_exit_fail(self):
        for label in ['wrong-mode','remote-F','stale-F','no-arrival','no-exit-input','early-ending']:
            rows=positive()
            if label=='wrong-mode':rows[4]['mode']='vehicle'
            if label=='remote-F':rows[4]['player']=[1,.14,1]
            if label=='stale-F':rows[3]['keys']=['E','F']
            if label=='no-arrival':rows[2]['vehicle']=[1,0,26]
            if label=='no-exit-input':rows[3]['keys']=[]
            if label=='early-ending':rows[1]['routeChapter'].update(stage=2,complete=True)
            with self.subTest(label=label):self.assertFalse(inspect_chapter(rows)['passed'])

    def test_moved_actor_parented_hidden_primitive_or_missing_observations_fail(self):
        for field,value in [('cachePosition',[51,.14,18]),('actorChild',True),
                            ('cacheActive',False),('originalMeshReuse',False),
                            ('componentCount',2),('valid',False),('rendererCount',0)]:
            rows=positive();rows[2]['routeChapter'][field]=value
            with self.subTest(field=field):self.assertFalse(inspect_chapter(rows)['passed'])
        rows=positive();rows[2].pop('routeChapter')
        self.assertFalse(inspect_chapter(rows)['passed'])

    def test_reset_must_clear_chapter_and_cannot_reuse_completion(self):
        rows=positive();rows[-1]['routeChapter'].update(stage=2,complete=True,cacheActive=True)
        rows.append(copy.deepcopy(rows[-1]));rows[-1]['time']=6.5;rows[-1]['keys']=[]
        self.assertFalse(inspect_chapter(rows)['passed'])
        rows=positive();rows[-1]['keys']=[]
        self.assertFalse(inspect_chapter(rows)['passed'])

    def test_activation_reset_is_scoped_and_cannot_count_as_complete_chapter(self):
        rows=[row(1),row(2,1,'vehicle',vehicle=[1,0,26]),row(3,0,keys=('R',),restart=1)]
        result=inspect_chapter(rows,require_complete=False)
        self.assertTrue(result['passed'],result)
        self.assertFalse(inspect_chapter(rows)['passed'])
        rows[1]['mission']='active'
        self.assertFalse(inspect_chapter(rows,require_complete=False)['passed'])

if __name__=='__main__':unittest.main()

