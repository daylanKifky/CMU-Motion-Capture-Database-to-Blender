import bpy, bmesh
from mathutils import *

D = bpy.data
C = bpy.context

def clean_empties():
	for ob in D.scenes['Scene'].objects:
			if ob.type == "EMPTY" or ob.type == "MESH":
				D.scenes['Scene'].objects.unlink(ob)


def bone_vec_to_world(vec):
	try:
		if vec.owner.id_data.type != "ARMATURE":
			raise Exception("The vector owner must be an Armature")
		
	except Exception as e:
		print("Can't convert bone vector to World space, probably the vector didn't belong to a bone, see error below")
		raise e

	ob = vec.owner.id_data
	bone = vec.owner.data

	m_vec  = Matrix()
	m_vec = m_vec.Translation(vec)
	m_vec = ob.convert_space(bone, m_vec, "POSE",  "WORLD")

	return m_vec.to_translation()
	#end bone_vec_to_world
	#

def bone_rot_to_world(rot):
	try:
		if rot.owner.id_data.type != "ARMATURE":
			raise Exception("The rotation owner must be an Armature")
		
	except Exception as e:
		print("Can't convert bone rotation to World space, probably the rotation didn't belong to a bone, see error below")
		raise e

	ob = rot.owner.id_data
	bone = rot.owner.data

	m_rot  = rot.to_matrix()
	# m_rot.Translation(rot)
	m_rot = ob.convert_space(bone, m_rot.to_4x4(), "LOCAL",  "WORLD")

	return m_rot.to_quaternion()
	#end bone_vec_to_world


def enter_edit_mode(ob):
	bpy.ops.object.mode_set(mode = 'OBJECT')
	bpy.ops.object.select_all(action = "DESELECT")
	ob.select = True
	bpy.context.scene.objects.active = ob
	bpy.ops.object.mode_set(mode = 'EDIT')



# Assign a collection
class BoneList(bpy.types.PropertyGroup):
    name = bpy.props.StringProperty(name="other_bone", default="")
    # value = bpy.props.IntProperty(name="Test Prop", default=22)

bpy.utils.register_class(BoneList)

bpy.types.Bone.others = \
    bpy.props.CollectionProperty(type=BoneList)


source = D.objects["SOURCE"]
target = D.objects["TARGET"]
bpy.ops.object.mode_set(mode = 'OBJECT')

relations = {\
		"Bone.004" : ("upperArm.L", "upperArm_rotate.L"),
	    "Bone.007" : ("foreArm.L", "foreArm_rotate.L"),
	    "Bone.005" : ("upperArm.R", "upperArm_rotate.R"),
	    "Bone.006" : ("foreArm.R", "foreArm_rotate.R")
    	}

magnitudes = {}

# clean_empties()


for rel in sorted(relations.items()):

	enter_edit_mode(target)
	bone = rel[0]

	print("POSITIONING: {}".format(bone))

	first = rel[1][0]

	second = rel[1][1]

	first = source.pose.bones[first]
	second = source.pose.bones[second]

	# Position
	a = bone_vec_to_world(first.head)
	b = bone_vec_to_world(second.tail)

	#Get the direction in LOCAL Space
	direction = b - a

	#CREATE SOME EMPTIES
	# bpy.ops.object.mode_set(mode = 'OBJECT')
	# bpy.ops.object.empty_add(location = a, radius = 0.2)
	# C.object.name = "%s_head" % first.head.owner.data.name 
	# C.object.show_name = True
	# bpy.ops.object.empty_add(location = b, radius = 0.2)
	# C.object.name = "%s_tail" % second.tail.owner.data.name
	# C.object.show_name = True 
	# enter_edit_mode(target)

	the_bone = target.data.edit_bones[bone]
	magnitude = the_bone.vector.magnitude

	the_bone.tail = the_bone.head + direction.normalized() * magnitude

	# Rotation
	f_rot = bone_rot_to_world(first.rotation_quaternion)
	s_rot = bone_rot_to_world(second.rotation_quaternion)

	quat = f_rot.slerp(s_rot, 0.5)

	#Extract twist
	axis = Vector(quat[1:])
	axis.normalize()

	ap = axis.project(direction)
	twist = Quaternion( (quat.w, ap.x, ap.y, ap.z)  )
	twist.normalize()

	the_bone.roll = - twist.angle
	print(twist.angle, " ", twist.axis)


# names = [source.data.bones[k].name for k in the_bone.others.keys()]

# quats = [source.data.bones[k].matrix.to_quaternion() for k in the_bone.others.keys()]

# quats_local = [source.data.bones[k].matrix_local.to_quaternion() for k in the_bone.others.keys()]

# locs = [source.data.bones[k].head_local for k in the_bone.others.keys()]
