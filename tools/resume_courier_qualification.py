#!/usr/bin/env python3
"""Resume sealed courier qualification once after diagnosed process-scan repair."""
from continue_game_queue import ContinuousRunner
from resume_three_day_queue import ThreeDayRunner, main
from qualify_visual_replay import qualify_saved_visual_candidate, verify_completed_native
from loop_controller.core import Halt
from loop_controller.continuous_tasks import TASKS
from loop_controller.delivery_policy import HARD_CAP_EPOCH

SOURCE = 'e45b26d6e84ac39f55a876e6aa43cddfec0c95d3'
ACCEPTED = 'd269dc43ac66c39afca4cb98ea53f9e7ed36806f'
ROUND = 'q0050-b46a1008'
BLOCKER = 'Halt: Capacity wait: engine handoff not granted; process/lease snapshot preserved'
COMPLETED = {
    "q0050-b46a1008": {
        "gate_sha256": "9227dead659a3692d26d3d9380c2b2d083bdfd2188018b8c26b7339944afbe39",
        "capture_manifest_sha256": "a3a86240a80cc35cfdb35ef87058e145611a3eeb6600cdd83de959c4bad11ed7",
        "build_id": "1709d40448b9b2d62294edac1aabbdb4b037707453dfc46b4555f966e77a2517"
    },
    "q0050-b46a1008-regression-walk": {
        "gate_sha256": "165becf1a1394b97eba9d1dcd6b649915c5046dd324c5b5c817a3beace1558e8",
        "capture_manifest_sha256": "23a495edb0a0fe187dcc7c1b877ca2a906c55bfffbd52a66c9f58a3b3e37ec33",
        "build_id": "b5bde7510173fac1d50031026b56626d2a5afd8aad7e268bca7c26dcfa7d2d2f"
    },
    "q0050-b46a1008-regression-world": {
        "gate_sha256": "9637d976b323d684136a7b10b1b18a253bc2296bc85acaf3dd909ddc3560e4e6",
        "capture_manifest_sha256": "985fb7432664c2733c3da8f94da9cc3dac072e463978a88da1ba8396264c8579",
        "build_id": "4799c3358a3f66d6d0bac54a2b57f7f7920eaa7d62053a3c79b74498f35d91cc"
    },
    "q0050-b46a1008-regression-motor": {
        "gate_sha256": "3bfea3374b3efd0959497d868e95091f36cd86509f296d52f7b6b2e07fc1255c",
        "capture_manifest_sha256": "2a031b578db61fd374b015176566e6ca299b1aee3a474a1d713b25b02ffaa2dd",
        "build_id": "2bc10c221d8bc2453619c0a1bd90fec81ebcd3f641e1d654e616db23dff80fd8"
    },
    "q0050-b46a1008-regression-courier": {
        "gate_sha256": "afc1ba6f6fc9be254c20f4d50762e34c50336744d0f130845689cc1c7f9a06e4",
        "capture_manifest_sha256": "644b60d0a790c54bbcd2336b76a8bc0a3849181ef8cb5b503b48b80a3a067a2b",
        "build_id": "526f9738fd2e8049ad81960766a57e6846365a2f5b945ad01c95a0476dbd8af6"
    },
    "q0050-b46a1008-regression-failure-retry": {
        "gate_sha256": "68ec61e63304835745f67d3ecac2880ffd1847fea25d06ec46d5e8962f6cdd14",
        "capture_manifest_sha256": "bc9525cb45baa5473ab93a8eb9de3eee2affdfb4a264257a39699b6e5c34167b",
        "build_id": "9f50b1047190bb0bfdf66d5287e8c15af31b713c67012e4c092eda4ed91d24d4"
    }
}
NEXT_MAP = (
    'Next milestone is a bounded connected Chicago map expansion, authored entirely by local Qwen. '
    'The accepted collision/pavement footprint is only X-1..6, Z-2..30 (7x32m); scenery outside it is not playable. '
    'Prioritize two connected street segments plus a traversable side alley; provisional measurable target '
    'at least60m along one axis and20m across, with actual continuous rendered support and collision boundaries. '
    'Start with one small connector extension; measure native scene bounds and normal-input traversal into it '
    'before adding the second segment. Keep the existing accepted core and all regression contracts functional. '
    'Do not count invisible support ground, decorations or repeated facade art as playable map area. '
    'Require real walking and driving across the old footprint into the connector and back, without falling, '
    'penetration or obstruction, and rendered frames that show its junction. Do not weaken old tests. '
    'After connected-space proof, add a second meaningful objective beyond the original corridor; then extend '
    'mission pacing toward8-12minutes through actual travel/objectives/pursuit, without idle padding. '
    'Camera/beacon/coupe/courier polish is not the next priority unless a measured regression blocks traversal. '
    'No final map-size or ten-minute acceptance until native evidence proves it; staged checkpoints only.'
)


def validate_pause(old):
    expected = dict(source_checkpoint=SOURCE, last_playable_checkpoint=ACCEPTED,
        current_round=ROUND, task_index=7, task_failures=7, failure_streak=1, diagnosis_used=True,
        overall_deadline_epoch=HARD_CAP_EPOCH, blocker=BLOCKER)
    if any(old.get(k) != v for k, v in expected.items()) or old.get('process_scan_recovery_attempted'):
        raise Halt('Expected the exact stopped q0050 infrastructure fault; preserve other failures')


class CourierQualificationResume(ThreeDayRunner):
    def validate_recovery(self, old):
        validate_pause(old)

    def recovery_settings(self):
        return {'process_scan_recovery_attempted': True}

    def native(self, task, ident, candidate, probe):
        prefix = ROUND + '-resumed-regression-'
        if ident.startswith(prefix):
            old_ident = ROUND + '-regression-' + ident[len(prefix):]
            if candidate != SOURCE or old_ident not in COMPLETED:
                raise Halt('No completed evidence for this native recovery')
            bundle = self.store.root / 'evidence' / old_ident
            gate = verify_completed_native(bundle, candidate, probe, COMPLETED[old_ident])
            self.store.event('reuse-completed-native', evidence=old_ident,
                candidate=candidate, **COMPLETED[old_ident])
            return bundle, gate
        return super().native(task, ident, candidate, probe)

    def regress(self, task, ident, candidate):
        # New suffix preserves the interrupted combat-foot build/capture directory.
        if ident == ROUND:
            return ContinuousRunner.regress(self, task, ident + '-resumed', candidate)
        return super().regress(task, ident, candidate)

    def work(self):
        self.machine.guard()
        self.store.event('resume-sealed-courier-qualification', candidate=SOURCE,
            completed_checks=list(COMPLETED), original_failure_counts_preserved=True,
            source_reauthored=False, original_partial_combat_preserved=True)
        if not qualify_saved_visual_candidate(self, TASKS[7], ROUND, SOURCE,
                completed_native=COMPLETED[ROUND]):
            raise Halt('Saved courier no longer qualifies for original-asset replay')
        self.store.set(task_design=NEXT_MAP,
            feedback={'visual_review': self.store.get('visual_focus_review'),
                      'next_required_milestone': NEXT_MAP})
        self.store.event('next-measurable-map-milestone', plan=NEXT_MAP,
            current_accepted_width_m=7, current_accepted_length_m=32,
            final_game_accepted=False)
        self.store.report()
        from qualify_map_extension import qualify_one_extension
        qualify_one_extension(self)
        self.store.set(task_design=NEXT_MAP,
            feedback={'accepted_connector': self.store.get('accepted_map_extension'),
                      'next_required_milestone': NEXT_MAP})
        return ContinuousRunner.work(self)


if __name__ == '__main__': raise SystemExit(main(CourierQualificationResume))
