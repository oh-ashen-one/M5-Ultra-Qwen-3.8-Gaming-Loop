from pathlib import Path
import json
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from loop_controller.adapters import Engines
from loop_controller.core import Store


class ExportProvenanceTests(unittest.TestCase):
    def run_export(self,root,exit_code):
        project=root/'game';(project/'Art').mkdir(parents=True)
        (project/'Art/player.py').write_text('import bpy\n')
        original=project/'ArtSources/player';original.mkdir(parents=True)
        generated=project/'Assets/Resources/Generated/player';generated.mkdir(parents=True)
        (original/'source.blend').write_bytes(b'old blend');(generated/'scene.fbx').write_bytes(b'old fbx')
        (original/'provenance.json').write_text('{"original":true}\n')
        class Machine:
            def execute(self,label,args,cwd,output,timeout,env,**kwargs):
                (output/'blender.log').write_text('failed' if exit_code else 'exported')
                if not exit_code:
                    (Path(env['LOOP_BLEND_SOURCE'])/'source.blend').write_bytes(b'new blend')
                    (Path(env['LOOP_ASSET_OUTPUT'])/'scene.fbx').write_bytes(b'new fbx')
                return exit_code
        store=Store(root/'run');engine=Engines(dict(blender='unused'),store,Machine(),root)
        result=engine.blender(project,'Art/player.py','attempt')
        return result,original,store.root/'artifacts/attempt'

    def test_failure_cannot_relabel_old_assets_as_new_source(self):
        with tempfile.TemporaryDirectory() as d:
            result,original,evidence=self.run_export(Path(d),7)
            self.assertFalse(result['ok'])
            self.assertEqual((original/'provenance.json').read_text(),'{"original":true}\n')
            self.assertEqual((original/'source.blend').read_bytes(),b'old blend')
            self.assertTrue((evidence/'export-failure.json').exists())

    def test_successful_manifest_and_preserved_copy_match(self):
        with tempfile.TemporaryDirectory() as d:
            result,original,evidence=self.run_export(Path(d),0)
            self.assertTrue(result['ok'])
            manifest=json.loads((original/'provenance.json').read_text())
            self.assertTrue(manifest['export_succeeded'])
            self.assertEqual(len(manifest['files']),2)
            self.assertEqual((original/'provenance.json').read_bytes(),
                (evidence/'editable-originals/provenance.json').read_bytes())


if __name__=='__main__':unittest.main()
