import bpy, bmesh
from mathutils import *

D = bpy.data

def clean_empties():
	for ob in D.scenes['Scene'].objects:
			if ob.type == "EMPTY" or ob.type == "MESH":
				D.scenes['Scene'].objects.unlink(ob)

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

bpy.ops.object.mode_set(mode = 'OBJECT')
bpy.ops.object.select_all(action = "DESELECT")
target.select = True
bpy.context.scene.objects.active = target
bpy.ops.object.mode_set(mode = 'EDIT')

for bone in relations:
	print("POSITIONING: {}".format(bone))

	first = relations[bone][0]
	
	second = relations[bone][1]

	first = source.data.bones[first]
	second = source.data.bones[second]

	# Position
	a = first.head_local
	b = second.tail_local
	direction = b - a

	the_bone = target.data.edit_bones[bone]
	magnitude = the_bone.vector.magnitude

	the_bone.tail = the_bone.head + direction.normalized() * magnitude

	# Rotation
	quat = first.matrix_local.to_quaternion().slerp(second.matrix_local.to_quaternion(),0.5)
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
