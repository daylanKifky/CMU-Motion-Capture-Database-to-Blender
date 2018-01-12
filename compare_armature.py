import bpy

C= bpy.context
D= bpy.data

# bpy.ops.object.armature_add(location=(0,0,0),layers=((False,)+(True,)+(False,)*18))

#keyframe coordinates (position in timeline, value)
#C.object.animation_data.action.fcurves[0].keyframe_points[0].co

#Property modified by fcurve
#C.object.animation_data.action.fcurves[3].data_path

#If multivalue property, index of the value modified by fcurve
#C.object.animation_data.action.fcurves[7].array_index


source = D.objects['SOURCE']
base = D.objects['BASE']


source.data.pose_position = 'REST'
base.data.pose_position = 'REST'

qsource = source.data.bones['RightShoulder'].matrix_local.to_quaternion()
qbase = base.data.bones['RightShoulder'].matrix_local.to_quaternion()

print("SOURCE: ", qsource)
print("BASE: " , qbase)

diff = qbase.rotation_difference(qsource)

print("DIF: " , diff.to_euler())

# base.data.edit_bones['RightShoulder'].transform(diff.to_matrix())

# print(base.data.bones['RightShoulder'].matrix_local.to_quaternion())


##############

def do_bone(pbone, target):
	#get the diff and store it on target
	pass




for pbone in source.pose.bones:
	# do_bone(pbone, base)
	pass