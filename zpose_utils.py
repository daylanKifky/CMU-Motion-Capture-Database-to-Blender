import bpy, bmesh
from bpy_extras import object_utils
from mathutils import *
from functools import cmp_to_key

from os import path
from sys import path as syspath
# syspath.append("/usr/lib/python3/dist-packages")
# from IPython import embed


# print(syspath)
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

def create_direction_obj(name, location, direction):
	mesh = bpy.data.meshes.new(name)
	bm = bmesh.new()
	v0 = bm.verts.new((0,0,0))
	v1 = bm.verts.new(direction)
	bm.edges.new((v0, v1))

	bm.to_mesh(mesh)
	mesh.update()

	ob = object_utils.object_data_add(bpy.context, mesh, name=name)
	ob = ob.object
	if location:
		ob.location = location

def get_basebone(arm):
		basebone = [b for b in arm.bones if b.parent is None]

		if len(basebone) != 1:
			raise Exception("The base armature has to have exactly one base bone")
		else:
			basebone = basebone[0]

		return basebone.name

def walk_bones(bone, handler):
	handler(bone)
	walk_childs_recursive(bone, handler)	

def walk_childs_recursive(bone, handler):
	for ch in bone.children:
		handler(ch)
		walk_childs_recursive(ch, handler)


def get_bone_co_pose_space(bone, tip_or_head):
        if type(bone) != bpy.types.Bone:
            raise TypeError("function expected a bone of type 'Bone', not", type(bone))
        # bone = self.target.data.bones[name]
        # 
        if tip_or_head.lower() == "tip":
            dest = Matrix.Translation(bone.tail)
        elif tip_or_head.lower() == "head":
            dest = Matrix.Translation(bone.head)
            
        if bone.parent:    
            Mptip = Matrix.Translation(bone.parent.tail - bone.parent.head)
            #head and orientation of parent bone
            Mw  = bone.parent.matrix_local
            #grandfather orientation
            Mw *= bone.parent.matrix.to_4x4().inverted()
            #tip of parent bone
            Mw *= Mptip
            #back to orientation of parent bone
            Mw *= bone.parent.matrix.to_4x4()
            #tip of bone
            Mw *= dest
            #orientation of bone
            Mw *= bone.matrix.to_4x4()    
        else:
            Mw = dest
            Mw *= bone.matrix.to_4x4()
            
        return Mw

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

	# print([b.name for b in bones], twist.axis.dot(direction))

	# embed()
	#__import__('code').interact(local={k: v for ns in (globals(), locals()) for k, v in ns.items()})

	# if twist.axis.dot(_zvec) >= 0:
	# 	return -twist.angle
	# else:
	return twist


def shortAngleDist(a0,a1):
    max = pi*2
    #max = 360
    da = (a1 - a0) % max
    return 2*da % max - da


def angleLerp(a0,a1,t):
    return a0 + shortAngleDist(a0,a1)*t

from math import pi
twopi = pi*2

def get_average_roll(bones, direction):
	"""bones is a list of tuples = (name, roll, direction_vector)"""
	direction = direction.copy()
	direction.normalize()
	total_roll = bones[0][1] * direction.dot(bones[0][2].normalized())
	# embed()
	for b in bones[1:]:
		# total_roll += b[1] * direction.dot(b[2].normalized()) / len(bones)
		total_roll = angleLerp(total_roll, b[1], direction.dot(b[2].normalized())) % twopi

	return total_roll



def clean_empties(keep):
	for ob in D.scenes['Scene'].objects:
		if ob.type in ["EMPTY", "MESH", "CURVE"]:
			if ob.name in keep:
				continue
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

#D.objects['SOURCE'].animation_data.action.fcurves[0].data_path == D.objects['SOURCE'].pose.bones['lumbar1'].path_from_id("location")
def get_fcurves(owner, prop):
    id_data = owner.id_data
    fcurves = []
    if not id_data.animation_data.action:
        return None

    for fcurve in id_data.animation_data.action.fcurves:
        if fcurve.data_path == owner.path_from_id(prop):
            fcurves.append(fcurve)
    return fcurves

def get_prop_values_at(owner, prop, index, absolute = False):
    fcurves = get_fcurves(owner, prop)
    if not fcurves:
        return owner.path_resolve(prop)

    fcurves.sort(key = lambda fc: fc.array_index, reverse=False)
    if absolute:
        scene_frames = {keypoints.co[0]: i for i,keypoints in enumerate(fcurves[0].keyframe_points)}
        index = scene_frames[index]
    result = []
    for fc in fcurves:
        result.append(fc.keyframe_points[index].co[1])
    return result 

def mode_set(who = bpy.context.object, context = bpy.context, mode="EDIT"):
    # debug("Mode set {} of {}".format(mode, who))
    if not bpy.ops.object.mode_set.poll():
    	return False

    bpy.ops.object.mode_set(mode = 'OBJECT')
    if mode == "OBJECT": return

    for ob in context.scene.objects:
    	if ob == who: continue
    	ob.select = False

    # if who == self.target or who in ("TARGET", "target", "Target"):
    #     who = self.target
    #     exiting = self.source
    # elif who == self.source or who in ("SOURCE", "source", "Source"):
    #     who = self.source
    #     exiting =self.target

    # exiting.select = False
    who.select = True
    context.scene.objects.active=who
    who.data.update_tag()
    context.scene.update()
    bpy.ops.object.mode_set(mode = mode)
    return True

def enter_edit_mode(ob):
	bpy.ops.object.mode_set(mode = 'OBJECT')
	bpy.ops.object.select_all(action = "DESELECT")
	ob.select = True
	bpy.context.scene.objects.active = ob
	bpy.ops.object.mode_set(mode = 'EDIT')


from time import sleep
class SimpleConfirmOperator(bpy.types.Operator):
    """Really?"""
    bl_idname = "armature.zpose_confirm_rotated"
    bl_label = "This operator doesn't work well on rotated armatures, continue anyway?"
    bl_options = {'REGISTER'}#{'REGISTER', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        # self.report({'WARNING'}, "Applying zpose conversion on rotated armatures")
        # self.wm = bpy.context.window_manager
        # tot = 100
        # for i in range(tot):
        #     self.wm.progress_update(i)
        #     sleep(0.01)
        # self.wm.progress_end()
        return {'FINISHED'}

    def invoke(self, context, event):
        self.wm = bpy.context.window_manager

        # progress from [0 - 1000]
        # tot = 100
        # self.wm.progress_begin(0, tot)
        self.execute(context)
        # return {"FINISHED"}
        return context.window_manager.invoke_confirm(self, event)

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
