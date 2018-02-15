import bpy, bmesh
from mathutils import *
from functools import cmp_to_key

D = bpy.data
C = bpy.context

verbosity = 0

def debug(*args):
	global verbosity
	if verbosity > 0:
		print(" ".join(map(str,args)))

def cmp_genealogy(this, other):
    if this.parent == other:
        debug(this.name, "is child of", other.name)
        return 1
    elif other in this.children_recursive :
        debug(this.name, "is parent of", other.name)
        return -1
    
    debug(this.name, "no relation", other.name)
    return 0

genealogy = cmp_to_key(cmp_genealogy)

def verify_chain(bones):
    for i,b in enumerate(bones):
        if i == 0: continue
        if b.parent != bones[i-1]:
            debug("Broken bone chain",i, b.parent.name, bones[i-1].name)
            return False
    return True


# _zvec = Vector((1,0,0))
def get_average_twist(bones, direction):
	# global _zvec
	
	quat = bone_rot_to_world(bones[0].rotation_quaternion)
	for b in bones[1:]:
		quat = bone_rot_to_world(b.rotation_quaternion).slerp(quat, 0.5)

	#Extract twist
	axis = Vector(quat[1:])
	axis.normalize()

	ap = axis.project(direction)
	twist = Quaternion( (quat.w, ap.x, ap.y, ap.z)  )
	twist.normalize()

	print([b.name for b in bones], twist.axis.dot(direction))
	#__import__('code').interact(local={k: v for ns in (globals(), locals()) for k, v in ns.items()})

	# if twist.axis.dot(_zvec) >= 0:
	# 	return -twist.angle
	# else:
	return twist.angle

def get_average_roll(bones, direction):
	total_roll = 0
	for b in bones:
		total_roll += b.roll * direction.dot(b.vector) / len(bones)

	return total_roll



def clean_empties():
	for ob in D.scenes['Scene'].objects:
			if ob.type == "EMPTY" or ob.type == "MESH":
				D.scenes['Scene'].objects.unlink(ob)


def bone_vec_to_world(vec):
	try:
		if vec.owner.id_data.type != "ARMATURE":
			raise Exception("The vector owner must be an Armature")
		
	except Exception as e:
		print("#"*30 + "\nCan't convert bone vector to World space, probably the vector didn't belong to a bone, see error below\n")
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


##########################
# TEST RUN
##########################
if __name__ == '__main__':
	

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
	# 
	iQuad = Quaternion((1,0,0,0))


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

		#Get the direction in WORLD Space
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

		swing = quat * twist.conjugated()

		if twist.axis.dot(Vector((0,0,1))) >= 0:
			the_bone.roll = -twist.angle
		else:
			the_bone.roll = twist.angle

		# print(twist.angle, " ", twist.axis, " ", twist.magnitude)
		print(twist.dot(iQuad), "<< DOT | ANGLE >> ", twist.axis.dot(Vector((0,0,1))))
		print("\n")
		# print(quat.dot(twist))


# names = [source.data.bones[k].name for k in the_bone.others.keys()]

# quats = [source.data.bones[k].matrix.to_quaternion() for k in the_bone.others.keys()]

# quats_local = [source.data.bones[k].matrix_local.to_quaternion() for k in the_bone.others.keys()]

# locs = [source.data.bones[k].head_local for k in the_bone.others.keys()]
