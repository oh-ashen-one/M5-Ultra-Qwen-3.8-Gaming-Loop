#!/usr/bin/env python3
"""Load corrected visual evidence selection at a saved-code boundary and retest."""
from continue_game_queue import ContinuousRunner
from resume_mission_fixture import main
from loop_controller.core import Halt, read_json
from loop_controller.continuous_checks import validate_proposed


class ReviewResume(ContinuousRunner):
    recovery_prefixes=('Halt: Requested stop','Halt: Replay-only role supplied no valid finish_task')
    recovery_description='Load state-based mission capture selection; retest saved local source with observed ordinary inputs'

    def prepare_resume(self,state,archive):
        stop=self.store.root/'STOP'
        if state.get('blocker')=='Halt: Requested stop':
            receipt=read_json(stop)
            if (receipt.get('purpose')!='review-selection-upgrade-after-complete-edit'
                    or receipt.get('saved_candidate')!=state['source_checkpoint']):
                raise Halt('Preserve a stop not owned by this specific saved-code reviewer migration')
            stop.rename(archive/'STOP')
        elif stop.exists():raise Halt('Preserve unexpected stop request')

    def edit(self,task,ident):
        if not self.store.get('provided_fixture_pending'):return super().edit(task,ident)
        probe=validate_proposed(self.store.get('last_valid_replay'),task['maximum'],task['coverage'])
        self.store.set(provided_fixture_pending=False)
        self.store.event('retest-saved-local-source',source=self.store.get('source_checkpoint'),
                         probe='Previously observed pickup/delivery/reset inputs; current source requalified natively',
                         game_source_mutation=False,review_capture_selection='actual mission states')
        return {'ok':True,'scenario':probe,'summary':'Retest preserved local source after external evidence-selection correction.'}


if __name__=='__main__':raise SystemExit(main(ReviewResume))
