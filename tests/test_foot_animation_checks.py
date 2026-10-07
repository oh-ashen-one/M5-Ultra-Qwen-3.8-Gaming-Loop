from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from loop_controller.foot_animation_checks import assess,clip_progress,horizontal_speed

class FootAnimationEvidence(unittest.TestCase):
    def test_imported_clips_and_actor_travel_are_insufficient(self):
        rows=[dict(time=i*.1,player=[i*.32,0,0],characterPresentation=dict(controllerHeight=1.75,
            controllerRadius=.32,visuals=[])) for i in range(181)]
        result=assess(rows,dict(animationType='Legacy',clips=[]))
        self.assertFalse(result['passed']);self.assertIn('no-measured-joint-motion-Walk',result['failures'])
        self.assertAlmostEqual(horizontal_speed(rows,4.1,5),3.2)
    def test_disabled_or_hidden_clip_does_not_prove_playback(self):
        rows=[]
        for i in range(10):
            clip=dict(name='Walk',playing=True,enabled=False,weight=1,time=i*.1)
            visual=dict(path='Player/PlayerVisual',active=True,clips=[clip])
            rows.append(dict(time=i*.1,characterPresentation=dict(visuals=[visual])))
        self.assertEqual(clip_progress(rows,'Walk',0,1)['samples'],0)
        for row in rows:
            row['characterPresentation']['visuals'][0]['clips'][0]['enabled']=True
        self.assertEqual(clip_progress(rows,'Walk',0,1)['samples'],10)
        for row in rows:row['characterPresentation']['visuals'][0]['active']=False
        self.assertEqual(clip_progress(rows,'Walk',0,1)['samples'],0)

if __name__=='__main__':unittest.main()
