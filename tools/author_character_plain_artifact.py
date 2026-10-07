#!/usr/bin/env python3
"""Save a complete bounded public Python artifact without a large tool envelope."""
from author_clothed_character import ACCEPTED, ART, TASK, SAVED, validate_art
from qualify_qwen_capacity import CapacityAuthor
from resume_three_day_queue import main
from loop_controller.core import Files, Halt, atomic, read_json, sha
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.visual_context import TARGETS, contract

PRIOR='q0186-a77bca7e'


def complete_source(response,max_lines=240,max_bytes=16000):
    choices=response.get('choices',[])
    if len(choices)!=1 or choices[0].get('finish_reason')!='stop':
        raise Halt('Only a completed public source artifact may be saved; no partial output')
    message=choices[0].get('message',{})
    if message.get('tool_calls'):
        raise Halt('Plain artifact request cannot replay tool calls')
    source=message.get('content')
    if not isinstance(source,str):raise Halt('Complete public Python source is missing')
    source=source.strip()
    if source.startswith('```python\n') and source.endswith('\n```'):
        source=source[len('```python\n'):-len('\n```')]
    if '<think>' in source or '</think>' in source or '```' in source:
        raise Halt('Never extract source from reasoning, marker replay or mixed prose')
    if len(source.splitlines())>max_lines or len(source.encode())>max_bytes:
        raise Halt(f'The bounded artifact must fit{max_lines}lines/{max_bytes}bytes')
    return validate_art(source+'\n')


class PlainCharacter(CapacityAuthor):
    def validate_recovery(self, old):
        expected=dict(status='paused',controller_pid=None,owned_process=None,
            source_checkpoint=ACCEPTED,last_playable_checkpoint=ACCEPTED,current_round=PRIOR,
            task_index=7,task_failures=24,failure_streak=1,diagnosis_used=True,
            overall_deadline_epoch=HARD_CAP_EPOCH,blocker="KeyError: 'choices'",
            clothed_character_budget_attempted=True)
        if any(old.get(k)!=v for k,v in expected.items()) or old.get('character_plain_artifact_attempted'):
            raise Halt('Require the diagnosed repeated tool-envelope fault and intact accepted fallback')
        self.faults={}
        for round_id in ('q0185-47b1c305',PRIOR):
            path=self.store.root/'private/sessions'/(round_id+'-clothed-character')/'response-000.json'
            response=read_json(path)
            if response.get('choices') or response.get('error',{}).get('code')!='incomplete_tool_call':
                raise Halt('Preserve any different response or completed tool work')
            self.faults[round_id]=sha(path.read_bytes())
        self.resume_capacity=self.priority_resume=self.transport_recovery=self.admission_recovery=False

    def recovery_settings(self):
        return dict(character_plain_artifact_attempted=True,
            recovery_route='compact-complete-public-source-without-tool-envelope',
            recovery_change='Both large serialized tool submissions ended incomplete with no source. Preserve them; do not repeat or expand the same request. Request one240line/16KB original model as final Python with no exposed tools, then validate and save only complete public content against the pinned source hash. Same supported xhigh/model/guards; no reasoning extraction.',
            character_tool_envelope_faults=self.faults)

    def work(self):
        ident=self.begin(TASK,'local-compact-character-artifact')
        files=Files(self.project,self.store);preimage=sha(files.path(ART).read_bytes())
        protected={p:sha(p.read_bytes()) for p in self.project.rglob('*.cs')}
        images=[('AI-GENERATED ART TARGET '+name+'; not game output',self.refs/name)
            for name in (TARGETS[0],TARGETS[2])]
        for label,path in [('actual front at92s','q0182-0282975a-death-active-runners/captures/frame-003.png'),
                           ('actual combat at107.6s','q0181-016a3dd5-success/captures/frame-005.png')]:
            images.append(('CURRENT NATIVE '+label,self.store.root/'evidence'/path))
        packet=contract(images,[TARGETS[0],TARGETS[2]],2)
        self.c.update(working_context_tokens=98304,output_tokens=32768,model_timeout_seconds=600)
        session=ident+'-compact-character'
        result=self.model.session('builder',session,
            'You are local Qwen, original Blender character author. Return one complete compact Python source artifact as your final content. No tools are available.',
            'Create a complete ORIGINAL clothed courier character in Blender5.2 using bpy/bmesh/mathutils. '
            'The supplied actual character is a segmented mannequin; the two references show the intended jacket, '
            'jeans, connected human proportions and aiming posture. This is the FIRST EARLY ARTIFACT, not the final '
            'full rig/animation deliverable. Keep it at most240lines/16KB. Use compact reusable mesh construction '
            'and shaped connected clothing forms: continuous jacket torso with collar/cuffs/hem, sleeves, dark-blue '
            'trousers, shoes, hands and proportionate head/hair. Avoid bead-like muscle ellipsoids. Reason only as '
            'needed to deliver compact complete code promptly. Do not design the whole game or write an essay.\n'
            'Make shoulder/elbow and hip/knee articulated empty pivots with clear stable names and concise local-axis '
            'comments so the NEXT saved increment can add Blender animation clips. No animation/controller code is '
            'needed in this first artifact. Use overlapping cloth joint construction that stays visually connected '
            'when bent. Original mesh only; no imported assets/textures/downloads. No cameras/lights/colliders. '
            'Clear the factory scene and create player_root. Blender meters, +Z up, +Y forward. Foot soles must be '
            'Z=.79 under root and anatomical height about1.8m: Unity instantiates the FBX and subtracts .79 from '
            'its localY. Use consistent parent-local transforms exactly once. Keep original capsule radius.32m '
            'and height1.75m in mind; do not enlarge the model to mimic reference camera scale. The accepted camera, '
            'reticle, controls and all C# stay unchanged. Name material colors distinctly; create your own surfaces. '
            'A simple original right-hand pistol may be included for later aim articulation.\n'
            'The fixed adapter saves .blend then FBX automatically, so do not read/write files or call import/export. '
            'Use only bpy,bmesh,math,mathutils (Euler.to_matrix API, not Matrix.Euler). Submit only the complete '
            'Python file in final content, optionally inside one python code fence. No XML, tool envelope, JSON, '
            'FILE markers or prose. The controller accepts only a completed response and parsed Python, then saves '
            'against the exact pinned old-file hash and exports immediately. The previous large tool envelopes '
            'were incomplete; this compact standalone artifact has32768output tokens with supported xhigh thinking. '
            'Do not spend the response on a detailed analysis of alternatives: make the smaller usable source.',
            [],{},images=images,turns=1,reasoning_effort='xhigh',visual_contract=packet,tool_choice='none')
        path=self.store.root/'private/sessions'/session/'response-000.json'
        source=complete_source(read_json(path))
        if sha(source.encode())==preimage:raise Halt('No new original character source')
        if any(sha(p.read_bytes())!=h for p,h in protected.items()):raise Halt('Protected gameplay changed')
        files.edit(ident+'-save-complete-public-artifact',ART,preimage,content=source)
        candidate=self.checkpoint_source('Local Qwen: save compact original clothed character artifact')
        outcome=dict(candidate=candidate,prior_playable=ACCEPTED,local_authored=True,script=ART,
            script_sha256=sha(source.encode()),native_verified=False,response_sha256=sha(path.read_bytes()),
            source_from='complete public final content only',tool_choice='none',reasoning_effort='xhigh',
            animation_integration='pending after early export/native inspection')
        atomic(self.store.root/'evidence'/(ident+'-character-source.json'),outcome)
        self.store.set(source_checkpoint=candidate,clothed_character_source_outcome=outcome,
            stage='clothed-character-source-saved');self.store.report()
        raise Halt(SAVED.removeprefix('Halt: '))


if __name__=='__main__':raise SystemExit(main(PlainCharacter))
