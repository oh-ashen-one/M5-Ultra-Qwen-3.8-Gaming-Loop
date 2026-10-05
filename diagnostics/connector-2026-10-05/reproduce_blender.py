"""Recreate the original local-Qwen diagnostic scene with existing Blender.

Run only on an authorized compute host under its shared engine admission lock:
blender --background --factory-startup --python reproduce_blender.py
This setup wrapper is cloud-authored; asset_scene.py is unchanged local Qwen code.
Outputs go beside this script. This is a connector fixture, not game content.
"""
from pathlib import Path
import bpy

root = Path(__file__).parent.resolve()
exec(compile((root / "asset_scene.py").read_text(), "asset_scene.py", "exec"))
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = 8
scene.render.threads_mode = "FIXED"
scene.render.threads = 8
scene.render.resolution_x = 512
scene.render.resolution_y = 512
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = str(root / "recreated-frame.png")
bpy.ops.wm.save_as_mainfile(filepath=str(root / "recreated-scene.blend"))
bpy.ops.export_scene.gltf(filepath=str(root / "recreated-scene.glb"), export_format="GLB")
bpy.ops.export_scene.fbx(filepath=str(root / "recreated-scene.fbx"),
                         use_selection=False, object_types={"MESH"}, add_leaf_bones=False)
bpy.ops.render.render(write_still=True)
