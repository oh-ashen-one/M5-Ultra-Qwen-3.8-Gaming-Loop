#!/usr/bin/env python3
"""Ask local Qwen to save two exact review corrections before native build."""
from qualify_qwen_capacity import CapacityAuthor
from submit_counter_exfil_parts import between,writes_shared_signals
from implement_counter_exfil import TASK,HUD,validate_source
from finish_counter_exfil_parts import RUNNER,ACCEPTED
from probe_counter_exfil import validate_boundary
from resume_three_day_queue import main
from loop_controller.core import Files,Halt,atomic,sha
from loop_controller.model import tool

SOURCE='8ca3b0d8c6c8bf3fad4b481dba2fd95f34c4e85c'

class RepairCounterReview(CapacityAuthor):
    def validate_recovery(self,old):
        validate_boundary(old)
        if (old.get('source_checkpoint')!=SOURCE or old.get('current_round')!='q0168-89945dfa'
                or old.get('counter_exfil_review_repair_attempted')):
            raise Halt('Require the completed local source and unattempted focused review correction')
        self.prior=old['counter_exfil_source_outcome']
        self.resume_capacity=self.priority_resume=self.transport_recovery=self.admission_recovery=False
    def recovery_settings(self):
        return dict(counter_exfil_review_repair_attempted=True,recovery_route='two-exact-local-source-review-fixes',
            recovery_change='Preserve complete local source. Correct the Collider API and unreachable Armed HUD branch in two selected spans; native acceptance remains pending.')
    def work(self):
        ident=self.begin(TASK,'local-counter-exfil-review-correction');files=Files(self.project,self.store)
        originals={p:files.path(p).read_text() for p in (RUNNER,HUD)}
        selected={RUNNER:between(originals[RUNNER],'        void TrimCoupeContacts()','        bool IsCoupe('),
            HUD:between(originals[HUD],'                if (_counter != null && _counter.BoardPriority)','                else if (_relay != null && _relay.Active)')}
        protected={str(p.relative_to(self.project)):sha(p.read_bytes()) for p in self.project.rglob('*')
            if p.is_file() and p.suffix in ('.cs','.shader','.fbx','.blend','.py') and str(p.relative_to(self.project)) not in originals}
        def save(action,fields):
            replacements={RUNNER:fields['runner_method'],HUD:fields['hud_branches']}
            for path,content in replacements.items():
                if not isinstance(content,str) or len(content.encode())>4000 or len(content.splitlines())>65:
                    raise ValueError('Return only the two bounded selected source spans')
                if not content.endswith('\n'):content+='\n'
                replacements[path]=content
                if content==selected[path]:raise ValueError('Save both actual corrections')
                validate_source(path,content)
                if writes_shared_signals(content):raise ValueError('Do not write shared signals')
            for path,content in replacements.items():
                files.edit(action+'-'+path.rsplit('/',1)[-1],path,sha(originals[path].encode()),old=selected[path],new=content)
            if any(sha(files.path(p).read_bytes())!=h for p,h in protected.items()):raise Halt('Protected source changed')
            candidate=self.checkpoint_source('Local Qwen: correct Counter-Exfil collider API and armed HUD priority')
            result=dict(ok=True,local_authored=True,candidate=candidate,changed_files=sorted(replacements),
                native_verified=False,source_sha256={p:sha(files.path(p).read_bytes()) for p in replacements})
            self.store.set(source_checkpoint=candidate);self.store.report();return result
        self.c.update(working_context_tokens=65536,output_tokens=8192,model_timeout_seconds=600)
        result=self.model.session('builder',ident+'-review-source',
            'You are local Qwen, sole gameplay author. Save the two small exact source corrections through finish_source now.',
            'Correct ONLY these selected spans. Collider inherits Component, so isActiveAndEnabled is not a '
            'Collider property. Preserve the null check, contact filtering and immediate hold clearing using '
            'the actual Collider.enabled and GameObject.activeInHierarchy APIs. Reference: '
            'https://docs.unity3d.com/6000.0/Documentation/ScriptReference/Collider.html\n'
            'The old InterceptionMission.Active remains true after Complete. In the supplied HUD branches '
            'that prevents Armed from ever appending its activation hint. Preserve new BoardPriority first, '
            'then make Armed show the old ending plus its one HudLine, then preserve the old Active fallback. '
            'Do not change any text, gameplay, source outside the spans or expand comments. Return exactly '
            'the full selected runner method and selected HUD branch chain through finish_source. The '
            'following else-if relay branch remains outside your replacement.\nRUNNER METHOD:\n'+selected[RUNNER]+
            '\nHUD BRANCHES:\n'+selected[HUD],
            [tool('finish_source','Save both exact selected C# spans and finish.',
                {'runner_method':{'type':'string'},'hud_branches':{'type':'string'}})],
            {'finish_source':save},turns=3,reasoning_effort='xhigh')
        atomic(self.store.root/'evidence'/(ident+'-review-source.json'),result)
        if not result.get('ok'):raise Halt('Preserve completed incident source; focused review correction incomplete')
        outcome=dict(self.prior,candidate=result['candidate'],review_correction=result)
        self.store.set(counter_exfil_source_outcome=outcome,counter_exfil_review_correction=result);self.store.report()
        raise Halt('Local Counter-Exfil source saved; unload idle inference and qualify actual inputs and negatives')

if __name__=='__main__':raise SystemExit(main(RepairCounterReview))
