#!/usr/bin/env python3
"""Repair measured relay source/API defects locally, preserving the failed build."""
import json
import re
from resume_ordered_relay import OrderedRelay
from resume_three_day_queue import main
from loop_controller.core import Files,Halt,sha
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.small_edits import SelectedEdit
from loop_controller.model import tool

SOURCE='42084b6ad9c5d41423899e738fe1938938ac1c41'
ROUND='q0110-eafc0e1f'
ACCEPTED='c9bbf1acc28a26c2a0d06a83da4d3b2b44cde188'
CORE='Assets/Game/RelaySequence.cs'
HUD='Assets/Game/RelaySequence.Hud.cs'
HASHES={CORE:'2a8dd05aae926610e6b0baccf3dda9be4efb12474bcd08895b1fe3054ff808f4',
    'Assets/Game/RelaySequence.Props.cs':'6d80cd4ec8a43f382a0a62fec537f3898e960d6c23ead3bb99bf7bdc6bd57538',
    HUD:'93160e1f7549afc756c905b62a8310ce8c23fb27f92f859456a5db6307dde312'}
GATE_SHA='58ba32e5dda0f1bc46e653b5d0cdd3f69538004be39e92009373afb910b80ff6'

def validate_pause(old):
    expected=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=ROUND,
        task_index=7,task_failures=24,failure_streak=1,diagnosis_used=True,second_street_attempts=4,
        overall_deadline_epoch=HARD_CAP_EPOCH,relay_microtasks_attempted=True,
        blocker='Halt: Relay positive requires measured diagnosis: "compile-build"')
    if any(old.get(k)!=v for k,v in expected.items()) or old.get('relay_source_repairs_attempted'):
        raise Halt('Require exact saved relay compile stop and preserved history')

class RelaySourceRepairs(OrderedRelay):
    def validate_recovery(self,old):
        validate_pause(old)
        for name,digest in HASHES.items():
            if sha((self.project/name).read_bytes())!=digest:raise Halt('Saved local relay partial changed: '+name)
        if sha((self.store.root/'evidence'/(ROUND+'-positive')/'relay-gate.json').read_bytes())!=GATE_SHA:
            raise Halt('Original compile evidence changed')

    def recovery_settings(self):
        return dict(relay_source_repairs_attempted=True,recovery_route='local-relay-api-and-latched-ending-repair',
            recovery_change='Preserve complete three-part local source and compiler errors; local tiny import/API/latch/readout corrections; passive child-TextMesh observer; native positive also checks ending remains complete beyond deadline.')

    def patch(self,ident,label,path,old,instruction,accept,max_lines=6):
        files=Files(self.project,self.store);raw=(self.project/path).read_text()
        if raw.count(old)!=1:raise Halt('Require one exact source span: '+label)
        first=raw[:raw.index(old)].count('\n')+1;last=first+len(old.splitlines())-1
        edit=SelectedEdit(files,path,first,last,max_lines=max_lines)
        def apply(action,f):
            content=f['content']
            if not accept(content,edit.old):raise ValueError('Keep the exact bounded '+label+' correction')
            return edit.apply(action,content)
        self.c.update(output_tokens=1536,model_timeout_seconds=110)
        self.store.set(stage='local-relay-repair-'+label);self.store.report()
        self.model.session('builder',ident+'-'+label,
            'You are local Qwen repairing your saved relay with one exact small edit. Call edit_selected_span now.',
            instruction+'\nEXACT SELECTED SOURCE:\n'+edit.old,
            [tool('edit_selected_span','Apply only this measured relay correction.',{'content':{'type':'string'}})],
            {'edit_selected_span':apply},turns=1,reasoning_effort='low')
        if (self.project/path).read_text()==raw:
            p=self.store.root/'private/sessions'/(ident+'-'+label)/'response-000.json'
            response=p.read_bytes();c=json.loads(response)['choices'][0];m=c['message'];content=m.get('content') or ''
            if c.get('finish_reason')!='stop' or m.get('tool_calls') or not accept(content,edit.old):
                raise Halt('Local bounded correction was not saved: '+label)
            edit.apply(ident+'-'+label+'-complete-public-source',content)
            self.store.event('complete-local-repair-recovered',label=label,response_sha256=sha(response),
                private_reasoning_used=False,original_response_preserved=True)
        candidate=self.checkpoint_source('Local Qwen: relay '+label)
        self.store.set(source_checkpoint=candidate,candidate_commit=candidate)

    def source(self,ident):
        self.patch(ident,'unity-import',CORE,'namespace ChicagoGame\n',
            'The native compiler cannot resolve MonoBehaviour, GameObject, Camera or Transform because this partial '
            'file has no UnityEngine import. Prepend using UnityEngine; and preserve namespace ChicagoGame exactly.',
            lambda content,old:re.sub(r'\s+','',content)=='usingUnityEngine;namespaceChicagoGame',3)
        raw=(self.project/CORE).read_text()
        line=next(s for s in raw.splitlines(True) if 'LoopInput.Mode' in s)
        self.patch(ident,'actual-mode-api',CORE,line,
            'LoopInput has Held/Pressed/MoveX/MoveY but NO Mode. Actual public static string Mode lives on LoopSignals. '
            'Change only LoopInput.Mode to LoopSignals.Mode. Keep the fresh F and foot condition unchanged.',
            lambda content,old:content.strip()==old.replace('LoopInput.Mode','LoopSignals.Mode').strip(),2)
        raw=(self.project/CORE).read_text();lines=raw.splitlines(True)
        i=next(i for i,s in enumerate(lines) if 'Remaining = UnityEngine.Mathf.Max' in s)
        block=''.join(lines[i:i+3])
        self.patch(ident,'latched-outcome',CORE,block,
            'The current countdown can mark a completed relay Failed after45seconds. Move the existing '
            'if (AllComplete || Failed) return; line BEFORE Remaining calculation and timeout check. '
            'Reorder ONLY these three lines, preserving their exact statements. Completion/failure remain latched until R.',
            lambda content,old:[s.strip() for s in content.splitlines() if s.strip()]==
                [old.splitlines()[2].strip(),old.splitlines()[0].strip(),old.splitlines()[1].strip()],4)
        raw=(self.project/HUD).read_text();line=next(s for s in raw.splitlines(True) if 'Mathf.RoundToInt(dist) + "F"' in s)
        self.patch(ident,'distance-controls',HUD,line,
            'Make the objective readable: change only the final string literal "F" to "m  F" so the distance has units '
            'and the interaction key is separated. No position/style/state changes.',
            lambda content,old:content.strip()==old.replace('+ "F"','+ "m  F"').strip(),2)
        return self.store.get('source_checkpoint')

if __name__=='__main__':raise SystemExit(main(RelaySourceRepairs))
