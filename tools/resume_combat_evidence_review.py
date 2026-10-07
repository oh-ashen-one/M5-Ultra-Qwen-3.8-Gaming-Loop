#!/usr/bin/env python3
"""Review unchanged qualified combat with compact, correctly attributed observations."""
import json
import uuid
from resume_three_day_queue import ThreeDayRunner,main
from loop_controller.core import Halt,atomic,read_json
from loop_controller.continuous_tasks import TASKS
from loop_controller.combat_checks import inspect_combat_contract
from loop_controller.delivery_policy import HARD_CAP_EPOCH

CANDIDATE='5034b67116838b8bc413acd40e9bb8d712bff623'
ACCEPTED='81659edb371a6b961d2e09983d88140b9c73d4ff'
PREFIX='combat-runtime-ae58a377-stable-'


class EvidenceReviewResume(ThreeDayRunner):
    def validate_recovery(self,old):
        if (old.get('source_checkpoint')!=CANDIDATE or old.get('last_playable_checkpoint')!=ACCEPTED or
            old.get('task_index')!=4 or old.get('task_failures')!=4 or old.get('failure_streak')!=1 or
            old.get('overall_deadline_epoch')!=HARD_CAP_EPOCH or old.get('blocker')!=
            'Halt: Third focused combat rejection; preserve evidence for bounded diagnosis, no generic planning round'):
            raise Halt('Expected the exact preserved scoped-critic context stop')

    def recovery_settings(self):return {'combat_review_recovery_pending':True}

    def work(self):
        ident='combat-evidence-review-'+uuid.uuid4().hex[:8];task=TASKS[4]
        bundle=self.store.root/'evidence'/(PREFIX+'combined');gate=read_json(bundle/'scoped-gate.json')
        if (not gate.get('passed') or gate.get('candidate_commit')!=CANDIDATE or
            not gate.get('regressions',{}).get('passed') or
            {x['test'] for x in gate['regressions']['regressions']}!={'walk','world','motor','courier','failure-retry'}):
            raise Halt('Preserved combined route and five regression receipts must match the current source')
        contracts=[]
        for kind in ('foot','wall','driving'):
            proof=self.store.root/'evidence'/(PREFIX+kind);original=read_json(proof/'combat-contract.json')
            if not original.get('passed') or original.get('candidate')!=CANDIDATE:raise Halt('Combat source proof mismatch')
            rows=[json.loads(line) for line in (proof/'captures/trace.jsonl').read_text().splitlines()]
            observed=inspect_combat_contract(rows,kind)
            observed.update(candidate=CANDIDATE,build_id=original['build_id'],evidence=original['evidence'],
                acceptance_fixture=original.get('acceptance_fixture'))
            if not observed['passed']:raise Halt('Newly explicit observed contract did not pass: '+kind)
            atomic(proof/'combat-contract-attributed.json',observed);contracts.append(observed)
        gate['combat_contracts']=contracts
        old=read_json(bundle/'critic.json')
        if old.get('bounded_stop')!='context':raise Halt('Do not overwrite a different critique')
        atomic(bundle/'critic-context-stop-preserved.json',old)
        atomic(bundle/'review-evidence-attributed.json',gate)
        self.store.set(stage='fresh-attributed-combat-review');self.store.report()
        review=self.review(task,ident,bundle,gate)
        if not review.get('ok'):raise Halt('Scoped review remains incomplete; source and prior records preserved')
        self.store.set(combat_review_recovery_pending=False)
        if review.get('verdict')=='PASS':
            self.promote(task,CANDIDATE,bundle,gate,review)
        else:
            self.reject_scoped(task,ident,review,CANDIDATE)
        # Continue the same queue. A FIX goes directly to local concrete edits;
        # a PASS advances normally. No verdict is silently upgraded.
        return super().work()


if __name__=='__main__':raise SystemExit(main(EvidenceReviewResume))
