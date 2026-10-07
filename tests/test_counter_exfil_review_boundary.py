from pathlib import Path
import copy
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from review_counter_exfil_incident import require_native,REGRESSIONS,counter_death,old_death
from loop_controller.core import Halt

class IncidentReviewBoundaryTests(unittest.TestCase):
    def fixture(self):
        def item(case):
            return dict(case=case,candidate='source',passed=True,build_id='build',evidence=case,
                native=dict(passed=True,candidate_commit='source',build_id='build'),gate=dict(passed=True))
        return dict(candidate='source',prior_native=dict(candidate='source',**{k:item(k) for k in ('old_healthy','activation_escape','success')}),
            success_continuity=item('success'),contact=item('contact'),
            counter_deaths=[item(k) for k in counter_death.CASES],old_deaths=[item(k) for k in old_death.CASES],
            regressions=dict(passed=True,regressions=[dict(test=k,gate=dict(passed=True,candidate_commit='source')) for k in REGRESSIONS]))
    def test_all_actual_sources_and_cases_required(self):
        good=self.fixture();require_native(good,'source')
        for mutate in [lambda d:d['counter_deaths'].pop(),lambda d:d['old_deaths'].append(copy.deepcopy(d['old_deaths'][0])),
                lambda d:d['contact'].update(passed=False),lambda d:d['success_continuity'].update(passed=False),
                lambda d:d['regressions']['regressions'][0]['gate'].update(candidate_commit='other'),
                lambda d:d['old_deaths'][0]['native'].update(candidate_commit='other'),
                lambda d:d['prior_native']['success']['native'].update(build_id='other')]:
            data=copy.deepcopy(good);mutate(data)
            with self.assertRaises(Halt):require_native(data,'source')

if __name__=='__main__':unittest.main()
