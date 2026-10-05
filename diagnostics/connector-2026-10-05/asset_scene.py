# Diagnostic scene: original red cube, blue UV sphere, gray ground.
# Uses only bpy and mathutils. No file/process ops; no save/export/render here;
# no bpy.data removal - scene cleared via select_all + object.delete.

import bpy
from mathutils import Vector

# --- Clear the current scene (no bpy.data removal) ---
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.ops.object.select_all(action='DESELECT')


def make_principled_material(name, color, roughness=0.4):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    for node in list(nodes):
        nodes.remove(node)
    out_node = nodes.new('ShaderNodeOutputMaterial')
    out_node.location = (300, 0)
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = (color[0], color[1], color[2], 1.0)
    bsdf.inputs['Roughness'].default_value = roughness
    links.new(bsdf.outputs['BSDF'], out_node.inputs['Surface'])
    return mat


# --- Original geometry ---
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-1.3, 0.0, 1.0))
cube = bpy.context.object
cube.name = 'RedCube'

bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, segments=32, ring_count=16, location=(1.3, 0.0, 1.0))
sphere = bpy.context.object
sphere.name = 'BlueSphere'
bpy.ops.object.shade_smooth()

bpy.ops.mesh.primitive_plane_add(size=12.0, location=(0.0, 0.0, 0.0))
ground = bpy.context.object
ground.name = 'GroundPlane'

# --- Node-based materials, roughness ~0.4 ---
mat_red = make_principled_material('RedCubeMat', (0.72, 0.04, 0.03))
mat_blue = make_principled_material('BlueSphereMat', (0.03, 0.10, 0.72))
mat_gray = make_principled_material('GroundGrayMat', (0.35, 0.35, 0.35))
cube.data.materials.append(mat_red)
sphere.data.materials.append(mat_blue)
ground.data.materials.append(mat_gray)

# --- World: subdued light ---
world = bpy.data.worlds.get('World')
if world is None:
    world = bpy.data.worlds.new('World')
bpy.context.scene.world = world
world.use_nodes = True
w_nodes = world.node_tree.nodes
w_links = world.node_tree.links
for node in list(w_nodes):
    w_nodes.remove(node)
w_out = w_nodes.new('ShaderNodeOutputWorld')
w_out.location = (300, 0)
w_bg = w_nodes.new('ShaderNodeBackground')
w_bg.location = (0, 0)
w_bg.inputs['Color'].default_value = (0.55, 0.57, 0.60, 1.0)
w_bg.inputs['Strength'].default_value = 0.35
w_links.new(w_bg.outputs['Background'], w_out.inputs['Surface'])

# --- Camera: (4, -7, 5) looking at (0, 0, 1), ortho scale 7 ---
cam_data = bpy.data.cameras.new('Camera')
cam_data.type = 'ORTHO'
cam_data.ortho_scale = 7.0
cam = bpy.data.objects.new('Camera', cam_data)
bpy.context.scene.collection.objects.link(cam)
cam.location = Vector((4.0, -7.0, 5.0))
direction = Vector((0.0, 0.0, 1.0)) - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
bpy.context.scene.camera = cam

# --- Large area light ---
light_data = bpy.data.lights.new('AreaLight', type='AREA')
light_data.shape = 'SQUARE'
light_data.size = 6.0
light_data.energy = 700.0
light = bpy.data.objects.new('AreaLight', light_data)
bpy.context.scene.collection.objects.link(light)
light.location = Vector((2.0, -3.0, 7.5))
light_direction = Vector((0.0, 0.0, 0.5)) - light.location
light.rotation_euler = light_direction.to_track_quat('-Z', 'Y').to_euler()

# --- Render settings: ensure full visibility ---
scene = bpy.context.scene
scene.render.resolution_x = 1280
scene.render.resolution_y = 720
scene.render.resolution_percentage = 100
try:
    scene.camera.clip_start = 0.05
    scene.camera.clip_end = 500.0
except AttributeError:
    pass
