import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from qualify_map_extension import inspect_extension
import resume_map_after_courier as recovery
import resume_map_plan_completion as plan_recovery
import resume_direct_map_builder as direct
import resume_map_spans as spans
import resume_pavement_completion as pavement
import resume_map_replay_case as replay_case
import resume_map_compile as map_compile
from loop_controller.core import Halt


class MapExtensionTests(unittest.TestCase):
    def test_lookup_span_preserves_inline_search_and_entire_loop_boundary(self):
        raw=('before\nTransform pv0 = null;\nforeach(var g in roots)\n{\n'
             'pv0 = FindDeep(g, "pavement"); if (pv0 != null) break;\n}\n'
             'if (pv0 != null)\n{\nuse(pv0);\n}\n')
        self.assertEqual(pavement.pavement_lookup_span(raw),(2,6))
        for bad in (raw+raw,raw.replace('if (pv0 != null)\n','if (other)\n')):
            with self.assertRaises(Halt):pavement.pavement_lookup_span(bad)

    def test_compile_recovery_keeps_rejection_counts_and_accepted_fallback(self):
        state=dict(source_checkpoint=map_compile.SOURCE,last_playable_checkpoint=map_compile.ACCEPTED,
            current_round=map_compile.ROUND,task_index=7,task_failures=9,failure_streak=1,
            diagnosis_used=True,overall_deadline_epoch=map_compile.HARD_CAP_EPOCH,
            blocker=map_compile.BLOCKER,map_replay_case_recovery_attempted=True)
        old=copy.deepcopy(state);map_compile.validate_compile_pause(state);self.assertEqual(state,old)
        for key,value in [('map_compile_recovery_attempted',True),('source_checkpoint','other'),
                          ('task_failures',0),('blocker','runtime fault')]:
            with self.subTest(key=key),self.assertRaises(Halt):
                map_compile.validate_compile_pause({**state,key:value})

    def test_saved_replay_recovery_requires_exact_stop_and_unchanged_proposal(self):
        state=dict(source_checkpoint=replay_case.SOURCE,last_playable_checkpoint=replay_case.ACCEPTED,
            current_round=replay_case.ROUND,task_index=7,task_failures=8,failure_streak=1,
            diagnosis_used=True,overall_deadline_epoch=replay_case.HARD_CAP_EPOCH,
            blocker=replay_case.BLOCKER,pavement_completion_attempted=True)
        old=copy.deepcopy(state);replay_case.validate_replay_pause(state);self.assertEqual(state,old)
        for key,value in [('map_replay_case_recovery_attempted',True),('source_checkpoint','other'),
                          ('task_failures',0),('blocker','runtime fault')]:
            with self.subTest(key=key),self.assertRaises(Halt):
                replay_case.validate_replay_pause({**state,key:value})
        with self.assertRaises(Halt):replay_case.saved_replay(b'changed original response')

    def test_pavement_completion_keeps_exact_stop_and_original_source(self):
        state=dict(source_checkpoint=pavement.SOURCE,last_playable_checkpoint=pavement.ACCEPTED,
            current_round=pavement.ROUND,task_index=7,task_failures=8,failure_streak=1,
            diagnosis_used=True,overall_deadline_epoch=pavement.HARD_CAP_EPOCH,
            blocker=pavement.BLOCKER,map_span_builder_attempted=True)
        old=copy.deepcopy(state);pavement.validate_pavement_pause(state);self.assertEqual(state,old)
        for key,value in [('pavement_completion_attempted',True),('source_checkpoint','other'),
                          ('task_failures',0),('blocker','runtime fault')]:
            with self.subTest(key=key),self.assertRaises(Halt):pavement.validate_pavement_pause({**state,key:value})
        with self.assertRaises(Halt):pavement.completed_proposal(b'changed original response')

    def test_smaller_spans_preserve_exact_whole_module_stop(self):
        state=dict(source_checkpoint=spans.SOURCE,last_playable_checkpoint=spans.ACCEPTED,
            current_round=spans.ROUND,task_index=7,task_failures=8,failure_streak=1,
            diagnosis_used=True,overall_deadline_epoch=spans.HARD_CAP_EPOCH,
            blocker=spans.BLOCKER,map_direct_builder_attempted=True)
        old=copy.deepcopy(state);spans.validate_span_pause(state);self.assertEqual(state,old)
        for key,value in [('map_span_builder_attempted',True),('source_checkpoint','other'),
                          ('task_failures',0),('blocker','resource fault')]:
            with self.subTest(key=key),self.assertRaises(Halt):spans.validate_span_pause({**state,key:value})

    def test_direct_builder_requires_exact_plan_output_stop_and_preserves_counters(self):
        state=dict(source_checkpoint=direct.SOURCE,last_playable_checkpoint=direct.ACCEPTED,
            current_round=direct.ROUND,task_index=7,task_failures=8,failure_streak=1,
            diagnosis_used=True,overall_deadline_epoch=direct.HARD_CAP_EPOCH,
            blocker=direct.BLOCKER,map_plan_completion_attempted=True)
        old=copy.deepcopy(state);direct.validate_direct_pause(state);self.assertEqual(state,old)
        for key,value in [('map_direct_builder_attempted',True),('map_extension_plan','present'),
                          ('source_checkpoint','other'),('task_failures',0),('blocker','memory fault')]:
            with self.subTest(key=key),self.assertRaises(Halt):direct.validate_direct_pause({**state,key:value})

    def test_direct_map_module_rejects_oversize_or_missing_callable_interface(self):
        valid='namespace ChicagoGame { public static class MapExtension { public static void Install(GameObject street) {} } }'
        self.assertEqual(direct.validate_module(valid),valid)
        for invalid in ['class Other {}',valid+'x'*10001,valid+chr(10)*171]:
            with self.assertRaises(ValueError):direct.validate_module(invalid)

    def test_read_only_plan_completion_is_one_time_and_exact(self):
        state=dict(source_checkpoint=plan_recovery.SOURCE,last_playable_checkpoint=plan_recovery.ACCEPTED,
            current_round=plan_recovery.ROUND,task_index=7,task_failures=8,failure_streak=1,
            diagnosis_used=True,overall_deadline_epoch=plan_recovery.HARD_CAP_EPOCH,
            blocker=plan_recovery.BLOCKER,map_after_courier_attempted=True)
        old=copy.deepcopy(state);plan_recovery.validate_plan_pause(state);self.assertEqual(state,old)
        for key,value in [('map_plan_completion_attempted',True),('map_extension_plan','already submitted'),
                          ('current_round','other'),('blocker','resource fault')]:
            with self.subTest(key=key),self.assertRaises(Halt):
                plan_recovery.validate_plan_pause({**state,key:value})

    def test_new_map_scope_preserves_exact_courier_rejection(self):
        state=dict(source_checkpoint=recovery.SOURCE,last_playable_checkpoint=recovery.ACCEPTED,
            current_round=recovery.ROUND,task_index=7,task_failures=8,failure_streak=1,
            diagnosis_used=True,overall_deadline_epoch=recovery.HARD_CAP_EPOCH,
            blocker=recovery.BLOCKER,process_scan_recovery_attempted=True)
        old=copy.deepcopy(state);recovery.validate_map_pause(state);self.assertEqual(state,old)
        for key,value in [('source_checkpoint','other'),('task_failures',0),
                          ('map_after_courier_attempted',True),('blocker','memory fault')]:
            with self.subTest(key=key),self.assertRaises(Halt):
                recovery.validate_map_pause({**state,key:value})

    def rows(self):
        rows=[]
        for mode in ['foot','vehicle']:
            # Continuous excursion six metres past the east boundary and back.
            for x in list(range(0,13))+[12]*12+list(range(11,-1,-1)):
                rows.append(dict(time=4+len(rows)*.1,mode=mode,player=[x,.14,10],
                    vehicle=[x,.14,10],grounded=True,playerCollisionEnabled=True,
                    vehicleCollisionEnabled=True,playerPenetration=0,vehiclePenetration=0,
                    restarts=0,keys=['W']))
        return rows

    def test_real_out_and_back_is_scoped_acceptance(self):
        result=inspect_extension(self.rows())
        self.assertTrue(result['passed'],result)
        self.assertEqual(result['traversal']['foot']['maximum_distance_beyond_old_boundary_m'],6)

    def test_old_corridor_alone_cannot_pass(self):
        rows=self.rows()
        for row in rows:row['player'][0]=min(row['player'][0],6);row['vehicle'][0]=min(row['vehicle'][0],6)
        self.assertFalse(inspect_extension(rows)['passed'])

    def test_reset_or_teleport_does_not_count_as_return(self):
        for reset in [True,False]:
            rows=self.rows()
            for row in rows[30:38]:
                if reset:row['restarts']=1;row['keys']=['R']
                else:row['player'][0]=0
            self.assertFalse(inspect_extension(rows)['passed'])

    def test_colliders_grounding_and_both_modes_required(self):
        for key,value in [('playerCollisionEnabled',False),('vehiclePenetration',1),('grounded',False)]:
            rows=self.rows()
            for row in rows:row[key]=value
            self.assertFalse(inspect_extension(rows)['passed'])
        self.assertFalse(inspect_extension([r for r in self.rows() if r['mode']=='foot'])['passed'])


if __name__=='__main__':unittest.main()
