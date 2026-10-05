#!/usr/bin/env python3
"""Continue the saved HUD/audio task using its accepted native input route."""
from pathlib import Path
from resume_three_day_queue import ThreeDayRunner,main
from loop_controller.core import Files,Halt,read_json,sha,verify_seal
from loop_controller.continuous_checks import validate_proposed
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.model import tool
from loop_controller.small_edits import SelectedEdit

CANDIDATE='202b53ba9ead65d120e621197fae6756ab92896b'
ACCEPTED='bbb0a9168aab596f5da3cabb6fdde4a0ccdb4b25'
REPLAY_STOP='Halt: Replay-only role supplied no valid finish_task; required: summary, duration, input_steps, captures'


def validate_hud_pause(old):
    if (old.get('source_checkpoint')!=CANDIDATE or old.get('last_playable_checkpoint')!=ACCEPTED
            or old.get('task_index')!=5 or old.get('task_failures')!=0 or old.get('failure_streak')!=0
            or old.get('overall_deadline_epoch')!=HARD_CAP_EPOCH or old.get('blocker')!=REPLAY_STOP):
        raise Halt('Expected the inspected q0025 HUD/audio replay-budget stop; preserve other faults')


def accepted_combat_probe(root,task,records):
    if task['id']!='mission-hud-audio':
        raise Halt('Accepted combat route reuse is limited to HUD/audio qualification')
    record=records.get('mission-combat-pursuit')
    if not record or record.get('scope')!='mission-combat-pursuit' or record.get('review',{}).get('verdict')!='PASS':
        raise Halt('Require the accepted combat/pursuit record')
    bundle=(Path(root)/record['evidence']).resolve()
    if not bundle.is_relative_to((Path(root)/'evidence').resolve()):
        raise Halt('Accepted replay evidence must remain inside the run')
    gate=read_json(bundle/'scoped-gate.json')
    if (not gate.get('passed') or gate.get('acceptance_fixture')
            or gate.get('scope')!='mission-combat-pursuit' or gate.get('candidate_commit')!=record['candidate']):
        raise Halt('Accepted replay gate provenance mismatch')
    captures=bundle/'captures'
    manifest=verify_seal(captures,sha((captures/'manifest.json').read_bytes()))
    if manifest.get('candidate')!=record['candidate'] or not any(x['path']=='scenario.json' for x in manifest['files']):
        raise Halt('Accepted input scenario must be sealed for its candidate')
    probe=validate_proposed(read_json(captures/'scenario.json'),task['maximum'],task['coverage'])
    return probe,record['evidence']


class HudAudioResume(ThreeDayRunner):
    def validate_recovery(self,old):validate_hud_pause(old)

    def recovery_settings(self):return {'hud_audio_install_pending':True}

    def reused_probe(self,task):
        probe,evidence=accepted_combat_probe(self.store.root,task,self.store.get('accepted_queue_features',{}))
        self.store.set(last_valid_replay=probe)
        self.store.event('reuse-accepted-combat-inputs',prior_evidence=evidence,
                         task=task['id'],current_source_requires_requalification=True,
                         success_claimed=False,game_source_mutation=False)
        return {'ok':True,'scenario':probe,'summary':'Retest current HUD/audio source with the accepted combat/courier inputs.'}

    def propose_replay(self,task,ident):
        if task['id']=='mission-hud-audio':return self.reused_probe(task)
        return super().propose_replay(task,ident)

    def edit(self,task,ident):
        if not self.store.get('hud_audio_install_pending'):return super().edit(task,ident)
        if task['id']!='mission-hud-audio':raise Halt('HUD/audio recovery cannot edit another task')
        # Verify old evidence before requesting even the bounded local source edit.
        self.reused_probe(task)
        files=Files(self.project,self.store);path='Assets/Game/Bootstrap.cs'
        lines=files.path(path).read_text().splitlines()
        found=[i for i,line in enumerate(lines) if line.strip()=='Combat.Install(body, cam);']
        if len(found)!=1:raise Halt('Expected the measured unique Bootstrap installation anchor')
        if any('AudioFX.Install(' in line or 'HudStatus.Install(' in line for line in lines):
            raise Halt('Preserve a source where HUD/audio installation already changed')
        edit=SelectedEdit(files,path,found[0]+1,found[0]+1,max_lines=4)
        self.c.update(output_tokens=2048,model_timeout_seconds=180)
        self.store.set(stage='local-hud-audio-install');self.store.report()
        self.model.session('builder',ident+'-install',
            'You are the sole local Qwen game author. Make one edit_selected_span call.',
            'Your saved AudioFX.cs and HudStatus.cs modules are not yet installed. In Bootstrap.Create, '
            'preserve the selected existing Combat installation and append calls to both existing modules. '
            'Their exact public signatures are AudioFX.Install(Transform rig) and HudStatus.Install(Camera cam). '
            'The live MainCamera GameObject is named rig, its Camera is cam, and rig already has an AudioListener. '
            'Use these existing objects; no new camera, listener, controls, geometry, gameplay signals or audio code. '
            'Return at most four source lines. Selected current span:\n'+edit.old,
            [tool('edit_selected_span','Replace only the selected installation span.',{'content':{'type':'string'}})],
            {'edit_selected_span':lambda action,f:edit.apply(action,f['content'])},
            turns=1,reasoning_effort='low')
        if sha(files.path(path).read_bytes())==edit.before:
            raise Halt('Local Qwen did not save the bounded HUD/audio installation')
        candidate=self.checkpoint_source('Local Qwen: install existing HUD and procedural audio')
        self.store.set(source_checkpoint=candidate,hud_audio_install_pending=False)
        self.store.event('hud-audio-local-install-saved',candidate=candidate,game_author='local Qwen')
        return self.reused_probe(task)


if __name__=='__main__':raise SystemExit(main(HudAudioResume))

