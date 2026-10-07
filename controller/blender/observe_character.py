"""Read-only pose/geometry evidence from the already saved original blend file.

Changing the evaluation frame does not author keys or save the scene. This
observer never creates/edits meshes, transforms, materials or animation data.
"""
import json
import os
from pathlib import Path
import bpy
from mathutils import Vector

FRAMES=(1,16,31,46,61,71,78,86,93,101,111,117,123,129,135,
        145,160,175,185,197,209,219,249,279)


def vector(v):
    return [float(x) for x in v]


def bounds(obj,depsgraph):
    evaluated=obj.evaluated_get(depsgraph)
    points=[evaluated.matrix_world@Vector(c) for c in evaluated.bound_box]
    low=[min(p[i] for p in points) for i in range(3)]
    high=[max(p[i] for p in points) for i in range(3)]
    return dict(min=low,max=high,center=[(a+b)/2 for a,b in zip(low,high)])


def main():
    scene=bpy.context.scene
    original=scene.frame_current
    result=dict(observer='external-passive-character-pose-observer',
        authored_animation=False,frames_per_second=scene.render.fps,
        frame_start=scene.frame_start,frame_end=scene.frame_end,samples=[])
    for frame in FRAMES:
        scene.frame_set(frame);bpy.context.view_layer.update()
        depsgraph=bpy.context.evaluated_depsgraph_get()
        sample=dict(frame=frame,joints=[],meshes=[])
        for obj in sorted(scene.objects,key=lambda o:o.name):
            if obj.type=='MESH':
                matrix=obj.evaluated_get(depsgraph).matrix_world.to_3x3()
                sample['meshes'].append(dict(name=obj.name,parent=obj.parent.name if obj.parent else None,
                    bounds=bounds(obj,depsgraph),local_y_world=vector(matrix@Vector((0,1,0))),
                    local_z_world=vector(matrix@Vector((0,0,1)))))
            elif obj.type in ('EMPTY','ARMATURE'):
                evaluated=obj.evaluated_get(depsgraph)
                sample['joints'].append(dict(name=obj.name,parent=obj.parent.name if obj.parent else None,
                    location=vector(obj.location),rotation_euler=vector(obj.rotation_euler),
                    world_position=vector(evaluated.matrix_world.translation)))
        result['samples'].append(sample)
    scene.frame_set(original)
    Path(os.environ['LOOP_RIG_OBSERVATION']).write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':main()
