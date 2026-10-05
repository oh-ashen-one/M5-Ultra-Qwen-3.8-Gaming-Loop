#!/usr/bin/env python3
"""One local-art correction for measured export/source drift and the visible end wall."""
from resume_visual_focus import VisualFocusResume, ACCEPTED
from resume_three_day_queue import main
from loop_controller.core import Halt
from loop_controller.delivery_policy import HARD_CAP_EPOCH

SOURCE = '694ab1deafdfb6de1c119a783c9ce01ae13b119c'


def validate_street_repair(old):
    expected = dict(source_checkpoint=SOURCE, last_playable_checkpoint=ACCEPTED, task_index=7,
                    task_failures=2, failure_streak=1, diagnosis_used=False,
                    overall_deadline_epoch=HARD_CAP_EPOCH,
                    blocker='Halt: Focused visual candidate regressed the integrated route; preserve evidence')
    if any(old.get(k) != v for k, v in expected.items()) or old.get('visual_export_repair_attempted'):
        raise Halt('Expected only the measured first street-export failure; preserve other stops')


class StreetExportRepair(VisualFocusResume):
    before_evidence = 'evidence/v0039-b0c9c536/captures/frame-000.png'

    def validate_recovery(self, old): validate_street_repair(old)
    def recovery_settings(self): return {'visual_export_repair_attempted': True}

    def choose_focus(self, ident, before):
        prior = self.store.get('visual_focus')
        if not prior or prior.get('asset') != 'Art/street.py':
            raise Halt('Preserve the existing local-Qwen-selected facade focus')
        correction = (
            'Measured correction from actual v0039 native evidence, not a gameplay redesign: '
            'the newly exported alley_wallW/E cross the accepted road. Their first world centers are '
            '(-3.10,2.80,12.85) and(-3.10,2.80,14.95), sizes(11.60,5.60,0.30); '
            'the car stops at Z10.55 under throttle instead of reachingZ27.85. These alley meshes were absent '
            'from the accepted102a2095 FBX even though the current Art script already contained their creation block. '
            'Re-export exposed that source/export mismatch. Fix the Art/street.py alley placement or remove that '
            'previously unexported alley section so the accepted X-1..6,Z-2..30 route remains physically open. '
            'Do not disable colliders, move anchors, widen targeting, or alter C# to pass the replay. '
            'The chosen large blank wall is the SOUTH END FACE of facade_wall, not its already windowed front. '
            'Measured mapping for the first module is worldX=-0.9-BlenderY, worldY=BlenderZ, worldZ=7+BlenderX; '
            'alley_wallW at Blender(5.85,2.2,2.8) confirms this. The visible end is therefore BlenderX=-6. '
            'Add real decorative window/brick/stone relief on that end plane, outward toward negativeBlenderX. '
            'Keep these decorations outside the playable pavement, with original facade_wall/base geometry intact. '
            'The previous added front mullions/piers did not improve the blank wall in before.png. '
            'Make a clearly visible architectural improvement to that exact face, not another minor front trim edit. '
            'Keep original Blender source and export provenance; one existing asset only.')
        focus = {**prior, 'local_gap_selection': prior['decision'], 'measured_correction': correction,
                 'correction_author': 'cloud controller, measured source/native geometry only'}
        self.store.set(visual_focus=focus)
        self.store.event('measured-street-export-diagnosis', evidence='evidence/v0039-b0c9c536',
            source=SOURCE, prior_local_choice_preserved=True, art_author='local Qwen',
            instructions=correction, original_failure_counts_preserved=True)
        return focus


if __name__ == '__main__': raise SystemExit(main(StreetExportRepair))
