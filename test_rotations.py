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

# a = Matrix()

# for parent in parents:
# 	a.rotate(parent.matrix)
# 	a *= Matrix().Translation(parent.tail)

txt = "RightShoulder"
parents = source.pose.bones[txt].parent_recursive.copy()
parents.reverse()
q = Quaternion()
q.identity()
for parent in parents:
	# last_q = q
	q *=  source.data.bones[parent.name].matrix.to_quaternion() * parent.rotation_quaternion

	# local_q = q * last_q.conjugated()

	print("{:20} global: {} | local: {}".format( parent.name, q, parent.rotation_quaternion ) )

	e = bpy.ops.object.empty_add(type='ARROWS', radius=0.3, view_align=False, 
	location=  parent.tail, rotation= q.to_euler(),
	layers=(True,) + (False,) * 19)

	C.object.name = parent.name
	C.object.show_name = True


e = bpy.ops.object.empty_add(type='ARROWS', radius=0.3, view_align=False, 
	location=  source.pose.bones[txt].tail, rotation= source.pose.bones[txt].matrix.to_euler(),
	layers=(True,) + (False,) * 19)


print("*"*20)
print(source.pose.bones[txt].parent.matrix.to_quaternion().conjugated() * source.pose.bones[txt].matrix.to_quaternion() )
print(source.pose.bones[txt].rotation_quaternion)


print("*"*20)
print(source.data.bones[txt].parent.matrix_local.to_quaternion().conjugated() * source.data.bones[txt].matrix_local.to_quaternion() )
print(source.data.bones[txt].matrix.to_quaternion())

# v = source.pose.bones[txt].head

# e = bpy.ops.object.empty_add(type='ARROWS', radius=0.4, view_align=False, 
# 	location=  v, rotation= (source.pose.bones[txt].rotation_quaternion).to_euler(),
# 	layers=(True,) + (False,) * 19)

# print(D.objects['SOURCE'].pose.bones[txt].matrix.to_euler())

# for bone in source.data.bones:
# # v = source.data.bones['lowerback'].center.copy().rotate(source.data.bones['Hips'].matrix)


# 	print(e)