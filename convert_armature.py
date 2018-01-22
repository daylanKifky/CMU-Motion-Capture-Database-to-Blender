import bpy
from math import degrees
from mathutils import Quaternion

# TODO
# -add root location, optionaly set root bone to 0
# -mind the armature object rotation!
# -parse the animation


C= bpy.context
D= bpy.data

def clean_empties():
	for ob in D.scenes['Scene'].objects:
			if ob.type == "EMPTY":
				D.scenes['Scene'].objects.unlink(ob)



class Armature_converter:
	"""Translates the animation of one armature to another with different base pose"""
	bpy.types.Bone.diff_quat = bpy.props.FloatVectorProperty(
			"Difference rotation", 
			subtype= "QUATERNION", 
			size = 4, 
			default=(1,0,0,0))

	# bpy.types.Bone.abs_diff_quat = bpy.props.FloatVectorProperty(
	# 		"Absolute Difference rotation", 
	# 		subtype= "QUATERNION", 
	# 		size = 4, 
	# 		default=(1,0,0,0))
	
	def __init__(self, source, target):
		self.source = D.objects['SOURCE']
		self.target = D.objects['BASE']

		self.set_poseposition("REST")

		bpy.ops.object.mode_set(mode = 'POSE')

		print("Converting armature {} to {}\n".format(source, target))


	def set_poseposition(self, mode = "POSE"):
		self.source.data.pose_position = mode
		self.target.data.pose_position = mode

	def get_basebone(self, where="source"):
		#ATTENTION!! source return data Bone, target returns PoseBone!
		if where == "source":
			basebone = [b for b in self.source.data.bones if b.parent is None]
		else:
			basebone = [b for b in self.target.pose.bones if b.parent is None]


		if len(basebone) != 1:
			raise Exception("The base armature has to have exactly one base bone")
		else:
			basebone = basebone[0]

		return basebone

	def reset_pose(self):
		a.get_basebone("target").rotation_quaternion.identity()
		a.walk_bones(a.get_basebone("target"), lambda b: b.rotation_quaternion.identity())

	def get_diff(self, bone):
		rot_bone =  bone.matrix.to_quaternion() 
		other = self.target.data.bones[bone.name]
		rot_other = other.matrix.to_quaternion()

		bone.diff_quat = rot_bone.rotation_difference( rot_other )

	def set_pose_from_diff(self, bone):
		self.target.pose \
				.bones[bone.name] \
				.rotation_quaternion *= bone.diff_quat.conjugated() \
										* self.source.pose.bones[bone.name].rotation_quaternion
		
		print("{:16} | {} | {}".format(bone.name, bone.diff_quat, bone.diff_quat))
	
	
	@staticmethod
	def walk_bones(bone, handler):
		for ch in bone.children:
			handler(ch)
			Armature_converter.walk_bones(ch, handler)

a = Armature_converter('SOURCE','BASE')
a.reset_pose()
a.walk_bones(a.get_basebone(), a.get_diff)

a.set_pose_from_diff(a.get_basebone())
a.walk_bones(a.get_basebone(), a.set_pose_from_diff)

a.set_poseposition()


# e = bpy.ops.object.empty_add(type='ARROWS', radius=0.3, view_align=False, 
		# 	location=  self.source.pose.bones[bone.name].tail, rotation= (diff.conjugated()).to_euler(),
		# 	layers=(True,) + (False,) * 19)

