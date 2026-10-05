#!/usr/bin/env python3
"""Load corrected visual evidence selection at a saved-code boundary and retest."""
from continue_game_queue import ContinuousRunner
from resume_mission_fixture import main
from loop_controller.core import Halt, read_json
from loop_controller.continuous_checks import validate_proposed


def verified_probe(root,task):
    candidates=sorted((root/'evidence').glob('*/scoped-gate.json'),key=lambda p:p.stat().st_mtime,reverse=True)
    for path in candidates:
        gate=read_json(path)
        if (gate.get('scope')=='connected-mission' and gate.get('passed')
                and gate.get('scoped_facts',{}).get('mission_anchors',{}).get('passed')
                and gate.get('scoped_facts',{}).get('courier_hud_states',{}).get('passed')):
            probe=validate_proposed(read_json(path.parent/'captures/scenario.json'),task['maximum'],task['coverage'])
            return probe,str(path.parent.relative_to(root))
    raise Halt('No previously verified pickup/delivery/reset probe; preserve the source for diagnosis')


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
        probe,evidence=verified_probe(self.store.root,task)
        self.store.set(provided_fixture_pending=False)
        self.store.event('retest-saved-local-source',source=self.store.get('source_checkpoint'),
                         probe='Previously observed pickup/delivery/reset inputs; current source requalified natively',
                         original_passing_evidence=evidence,game_source_mutation=False,
                         review_capture_selection='actual mission states')
        return {'ok':True,'scenario':probe,'summary':'Retest preserved local source after external evidence-selection correction.'}


if __name__=='__main__':raise SystemExit(main(ReviewResume))
