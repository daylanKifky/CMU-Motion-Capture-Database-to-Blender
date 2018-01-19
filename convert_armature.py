import bpy
from math import degrees


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

	def get_basebone(self):
		basebone = [b for b in self.source.data.bones if b.parent is None]

		if len(basebone) != 1:
			raise Exception("The base armature has to have exactly one base bone")
		else:
			basebone = basebone[0]

		return basebone


	def get_abs_diff(self, bone):
		rot_bone =  bone.matrix.to_quaternion() 
		# rot_bone = bone.matrix.to_quaternion()
		other = self.target.data.bones[bone.name]
		rot_other = other.matrix.to_quaternion()
		# rot_other = other.matrix.to_quaternion()

		diff = rot_bone.rotation_difference( rot_other )

		# e = bpy.ops.object.empty_add(type='ARROWS', radius=0.3, view_align=False, 
		# 	location=  self.source.pose.bones[bone.name].tail, rotation= (diff.conjugated()).to_euler(),
		# 	layers=(True,) + (False,) * 19)

		self.target.pose.bones[bone.name].rotation_quaternion *= diff.conjugated() * self.source.pose.bones[bone.name].rotation_quaternion
		print("{:16} | {} | {}".format(bone.name, diff, diff.angle))
	
	
	@staticmethod
	def walk_bones(bone, handler):
		# handler(bone)
		for ch in bone.children:
			# if ch.name == "RightShoulder": omit = False
			handler(ch)
			Armature_converter.walk_bones(ch, handler)

a = Armature_converter('SOURCE','BASE')
a.walk_bones(a.get_basebone(), a.get_abs_diff)
a.set_poseposition()
# a.debug(a.get_basebone())
# a.walk_bones(a.get_basebone(), a.debug)
# print("SECONDA PASSATA")
# a.walk_bones(a.get_basebone(), a.set_relative_diff)
# a.walk_bones(a.get_basebone(), a.get_diff_prop)


