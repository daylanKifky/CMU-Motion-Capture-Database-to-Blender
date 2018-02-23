import bpy
from mathutils import *

C= bpy.context
D= bpy.data

# bpy.ops.object.armature_add(location=(0,0,0),layers=((False,)+(True,)+(False,)*18))

#keyframe coordinates (position in timeline, value)
#C.object.animation_data.action.fcurves[0].keyframe_points[0].co

#Property modified by fcurve
#C.object.animation_data.action.fcurves[3].data_path

#If multivalue property, index of the value modified by fcurve
#C.object.animation_data.action.fcurves[7].array_index
#
#Insert keyframe        
#D.objects['Suzanne'].keyframe_insert("rotation_quaternion",index=-1, frame=bpy.context.scene.frame_current, group="Rotation")


source = D.objects['SOURCE']
# base = D.objects['BASE']

# print(source.data.bones['Hips'].matrix)
# v.rotate(source.data.bones['Hips'].matrix)
# print(v)

# v = source.data.bones['Chest'].center.copy()
# parents = source.data.bones['Chest'].parent_recursive.copy()
# parents.reverse()

# a = Matrix()

# for parent in parents:
# 	a.rotate(parent.matrix)
# 	a *= Matrix().Translation(parent.tail)

txt = "RightElbow"


v = D.objects['SOURCE'].pose.bones[txt].head

e = bpy.ops.object.empty_add(type='ARROWS', radius=1, view_align=False, 
	location=  v, rotation= D.objects['SOURCE'].pose.bones[txt].matrix.to_euler(),
	layers=(True,) + (False,) * 19)

print(D.objects['SOURCE'].pose.bones[txt].matrix.to_euler())

# for bone in source.data.bones:
# # v = source.data.bones['lowerback'].center.copy().rotate(source.data.bones['Hips'].matrix)


# 	print(e)