import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from loop_controller.street_detail_checks import inspect_details,PREFIX
from resume_chapter_review_street_details import validate_module,validate_pause,SOURCE,ROUND,ACCEPTED
from loop_controller.core import Halt
from loop_controller.delivery_policy import HARD_CAP_EPOCH

class StreetDetailTests(unittest.TestCase):
    def fixture(self):
        before=[dict(name='WorldCollision/StreetSouthWall',kind='BoxCollider',enabled=True,
                     boundsCenter=[41,4.4,7.75],boundsSize=[38,8.8,.5])]
        added=[]
        for region,center in [('South',[30,3,8.1]),('North',[30,3,27.9]),('East',[59.9,3,18])]:
            for i in range(40):
                family=['win','door','cornice','pier'][i%4]
                added.append(dict(name=PREFIX+region+'-0/'+family+str(i),kind='renderer',enabled=True,
                                  boundsCenter=center.copy(),boundsSize=[.1,.2,.1]))
        return before,before+added

    def test_native_detail_gate_requires_existing_geometry_and_clear_three_sides(self):
        before,after=self.fixture();self.assertTrue(inspect_details(before,after)['passed'])
        for mutation in ('wall','collider','interior','nonfinite','missing','families'):
            bad=copy.deepcopy(after)
            if mutation=='wall':bad[0]['boundsSize'][0]=1
            if mutation=='collider':bad[1]['kind']='BoxCollider'
            if mutation=='interior':bad[1]['boundsCenter'][2]=15
            if mutation=='nonfinite':bad[1]['boundsSize'][0]=float('nan')
            if mutation=='missing':bad=bad[:70]
            if mutation=='families':
                for o in bad[1:]:o['name']=o['name'].replace('/cornice','/blank')
            with self.subTest(mutation=mutation):self.assertFalse(inspect_details(before,bad)['passed'])

    def test_source_scope_rejects_physics_harness_and_whole_scene_clones(self):
        source='class EastStreetDetail { void Install(GameObject parent) { /* sharedMesh sharedMaterials South North East */ } }'
        self.assertEqual(validate_module(source),source)
        for token in ['LoopSignals','Collider','Instantiate','Destroy','CreatePrimitive','Resources.Load']:
            with self.subTest(token=token),self.assertRaises(ValueError):validate_module(source+token)

    def test_resume_cannot_erase_visual_fix_or_reset_failure_budget(self):
        state=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=ROUND,
            task_index=7,task_failures=24,failure_streak=1,diagnosis_used=True,second_street_attempts=4,
            overall_deadline_epoch=HARD_CAP_EPOCH,
            blocker='Halt: East Dead-Drop scoped qualification recorded; preserve broader visual FIX and continue connected pacing',
            east_dead_drop_outcome=dict(native_pass=True,accepted=False,review={'verdict':'FIX'}))
        validate_pause(state)
        for key,value in [('task_failures',0),('last_playable_checkpoint',SOURCE),
                          ('chapter_review_street_details_attempted',True),('overall_deadline_epoch',HARD_CAP_EPOCH+1)]:
            with self.subTest(key=key),self.assertRaises(Halt):validate_pause({**state,key:value})

if __name__=='__main__':unittest.main()
