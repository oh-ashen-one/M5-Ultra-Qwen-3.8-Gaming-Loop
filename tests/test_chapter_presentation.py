import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from loop_controller.chapter_presentation import inspect_presentation
from resume_chapter_presentation import validate_visual_span,visual_probe,validate_pause,SOURCE,ROUND,ACCEPTED
from loop_controller.core import Halt
from loop_controller.delivery_policy import HARD_CAP_EPOCH

class ChapterPresentationTests(unittest.TestCase):
    def rows(self):
        panels=[dict(name=n,visible=True,text=n,textRect=t,cardRect=c) for n,t,c in [
            ('RouteHud',[.52,.81,.90,.88],[.50,.79,.92,.90]),
            ('MissionHud',[.08,.09,.30,.14],[.05,.07,.40,.16]),
            ('HudStatus',[.06,.84,.21,.88],[.04,.81,.31,.91])]]
        rows=[]
        for t in range(1,15):
            stage=0 if t==1 or t>=11 else (2 if t==10 else 1)
            rows.append(dict(time=t,restarts=int(t>=11),routeChapter=dict(stage=stage,hudPanels=copy.deepcopy(panels),
                cacheBoundsCenter=[50,1.14,18],cacheBoundsSize=[2,2,1.5],emissiveRenderers=1)))
        return rows

    def test_real_projected_panels_and_cache_bounds_pass(self):
        check=inspect_presentation(self.rows());self.assertTrue(check['passed']);self.assertEqual(check['reset_samples'],4)

    def test_overlap_clipping_tiny_text_float_and_full_prop_emission_fail(self):
        for defect in ['overlap','clipped','tiny','floating','misaligned','emission','unobserved','reset']:
            rows=self.rows();v=rows[3]['routeChapter'];p=v['hudPanels'][0]
            if defect=='overlap':p['cardRect']=[.04,.8,.4,.95]
            if defect=='clipped':p['cardRect'][3]=1.1
            if defect=='tiny':p['textRect'][3]=.82
            if defect=='floating':v['cacheBoundsCenter'][1]=3
            if defect=='misaligned':v['cacheBoundsCenter'][0]=51
            if defect=='emission':v['emissiveRenderers']=5
            if defect=='unobserved':v['cacheBoundsSize']=[]
            if defect=='reset':rows[-1]['routeChapter']['hudPanels'][1]['textRect'][3]=.2
            with self.subTest(defect=defect):self.assertFalse(inspect_presentation(rows)['passed'])

    def test_visual_edits_cannot_change_gameplay_or_hide_legacy_receipt(self):
        validate_visual_span('if (card != null) card.gameObject.SetActive(false);')
        for raw in ['RouteStage = 2;','RouteComplete=true;','Cache=anchor.transform;','Objective="done";',
                    'LoopInput.Replay;', 'missionHud.gameObject.SetActive(false);','void Update() {}']:
            with self.subTest(raw=raw),self.assertRaises(ValueError):validate_visual_span(raw)
        with self.assertRaises(ValueError):validate_visual_span('foreach (var c in GetComponents<Collider>()) {}',True)

    def test_exact_input_reuse_only_adds_an_interaction_capture(self):
        old=dict(duration=36,steps=[dict(start=4,end=5,keys=['W'])],captures=[3,31,33,35])
        before=copy.deepcopy(old);new=visual_probe(old)
        self.assertEqual(old,before);self.assertEqual(new['steps'],old['steps']);self.assertEqual(new['duration'],old['duration'])
        self.assertEqual(new['captures'],[3,31,32.55,33,35])

    def test_only_hash_pinned_complete_hud_can_be_recovered_inside_visual_bound(self):
        import json
        from unittest.mock import patch
        from loop_controller.core import sha
        import resume_saved_compact_hud as saved
        content='// local visual line\n'*130
        value={'choices':[{'finish_reason':'tool_calls','message':{'tool_calls':[
            {'function':{'name':'edit_selected_span','arguments':json.dumps({'content':content})}}]}}]}
        raw=json.dumps(value).encode()
        with patch.object(saved,'RESPONSE_SHA',sha(raw)):
            self.assertEqual(saved.saved_proposal(raw),content)
            with self.assertRaises(Halt):saved.saved_proposal(raw+b' ')
        value['choices'][0]['finish_reason']='length';raw=json.dumps(value).encode()
        with patch.object(saved,'RESPONSE_SHA',sha(raw)),self.assertRaises(Halt):saved.saved_proposal(raw)
        with self.assertRaises(ValueError):validate_visual_span('// line\n'*141)

    def test_scope_resume_preserves_exact_baseline_budget_and_prior_verdict(self):
        state=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=ROUND,
            task_index=7,task_failures=24,failure_streak=1,diagnosis_used=True,second_street_attempts=4,
            overall_deadline_epoch=HARD_CAP_EPOCH,
            blocker='Halt: East street facade scope recorded; connected mission pacing and outstanding presentation remain',
            east_street_facade_outcome=dict(accepted=True,review={'verdict':'PASS'}))
        validate_pause(state)
        for key,value in [('task_failures',0),('last_playable_checkpoint',SOURCE),('chapter_presentation_attempted',True)]:
            with self.subTest(key=key),self.assertRaises(Halt):validate_pause({**state,key:value})

if __name__=='__main__':unittest.main()
