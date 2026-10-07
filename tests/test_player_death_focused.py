import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from resume_player_death_focused import (ACCEPTED, AUTHORITY, BOOT, FOLLOW, HARD_CAP_EPOCH,
    PARTIAL, validate_boundary, validate_edit)
from loop_controller.core import Halt


class FocusedDeathTests(unittest.TestCase):
    def boundary(self):
        return dict(status='paused',controller_pid=None,owned_process=None,source_checkpoint=PARTIAL,
            current_round='q0143-c432e36d',last_playable_checkpoint=ACCEPTED,task_index=7,
            task_failures=24,failure_streak=1,diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,
            player_death_source_attempted=True,blocker='URLError: <urlopen error [Errno 61] Connection refused>',
            player_death_source_fault=dict(candidate=PARTIAL,complete_integration=False,
                cause='resident available-memory guard'),player_death_red_outcome=dict(all_setups_valid=True))

    def test_only_diagnosed_stopped_partial_can_resume(self):
        valid=self.boundary();validate_boundary(valid)
        for changed in [dict(controller_pid=42),dict(owned_process={'pid':42}),
                dict(source_checkpoint='different'),dict(last_playable_checkpoint='different'),
                dict(player_death_focused_attempted=True),dict(task_failures=0)]:
            with self.subTest(changed=changed),self.assertRaises(Halt):validate_boundary({**valid,**changed})
        wrong=copy.deepcopy(valid);wrong['player_death_source_fault']['cause']='unknown'
        with self.assertRaises(Halt):validate_boundary(wrong)

    def test_camera_and_other_phase_source_remain_protected(self):
        camera=' { qualified camera and reticle }'
        validate_edit(BOOT,'updated walker\n'+FOLLOW+camera,{BOOT},camera)
        with self.assertRaises(ValueError):validate_edit(BOOT,'walker\n'+FOLLOW+'changed',{BOOT},camera)
        with self.assertRaises(ValueError):validate_edit(AUTHORITY,'class DeathAuthority {}',{BOOT},camera)

    def test_acceptance_manipulation_is_rejected(self):
        for fragment in ['LoopPlayerDeathFixture','LoopInput.Replay','GetCommandLineArgs','Time.timeScale']:
            with self.subTest(fragment=fragment),self.assertRaises(ValueError):
                validate_edit(AUTHORITY,'class DeathAuthority { '+fragment+' }',{AUTHORITY},'')

    def test_authority_requires_small_concrete_api_source(self):
        validate_edit(AUTHORITY,'class DeathAuthority { bool dead; }',{AUTHORITY},'')
        for source in ['using System.Reflection; class DeathAuthority {}',
                'class DeathAuthority {}\n'+'\n'*160,'class Other {}']:
            with self.subTest(source=source[:35]),self.assertRaises(ValueError):
                validate_edit(AUTHORITY,source,{AUTHORITY},'')


if __name__=='__main__':unittest.main()
