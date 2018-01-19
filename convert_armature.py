import bpy
from math import degrees


C= bpy.context
D= bpy.data


omit = False



class Armature_converter:
	"""Translates the animation of one armature to another with different base pose"""
	bpy.types.Bone.diff_quat = bpy.props.FloatVectorProperty(
			"Difference rotation", 
			subtype= "QUATERNION", 
			size = 4, 
			default=(1,0,0,0))

	bpy.types.Bone.abs_diff_quat = bpy.props.FloatVectorProperty(
			"Absolute Difference rotation", 
			subtype= "QUATERNION", 
			size = 4, 
			default=(1,0,0,0))
	
	def __init__(self, source, target):
		self.source = D.objects['SOURCE']
		self.target = D.objects['BASE']

		self.source.data.pose_position = "REST"
		self.target.data.pose_position = "REST"

		bpy.ops.object.mode_set(mode = 'POSE')

		# for ob in D.scenes['Scene'].objects:
		# 	if ob.type == "EMPTY":
		# 		D.scenes['Scene'].objects.unlink(ob)

		print("Converting armature {} to {}\n".format(source, target))


	def set_posemode(self):
		self.source.data.pose_position = "POSE"
		self.target.data.pose_position = "POSE"

	def get_basebone(self):
		basebone = [b for b in self.source.data.bones if b.parent is None]

		if len(basebone) != 1:
			raise Exception("The base armature has to have exactly one base bone")
		else:
			basebone = basebone[0]

		return basebone


	def get_abs_diff(self, bone):
		# qbase = self.target.data.bones[bone.name].matrix_local.to_quaternion()

		# self.target.data.bones[bone.name].abs_diff_quat = diff 
		 
		# s_bone = self.source.convert_space(pose_bone = bone,
		# 									matrix= bone.matrix,
		# 									from_space="WORLD",
		# 									to_space="LOCAL_WITH_PARENT" )

		# other = self.target.pose.bones[bone.name]

		# t_bone = self.target.convert_space(pose_bone = other,
		# 									matrix= other.matrix,
		# 									from_space="WORLD",
		# 									to_space="LOCAL_WITH_PARENT" )

		
		# diff = bone \
		# 		.matrix \
		# 		.to_quaternion() \
		# 		.rotation_difference( self.target.pose.bones[bone.name].matrix.to_quaternion() )
		
		# diff = bone.parent \
		# 		.matrix \
		# 		.to_quaternion() *diff


		rot_bone =  bone.matrix.to_quaternion() 
		# rot_bone = bone.matrix.to_quaternion()
		other = self.target.data.bones[bone.name]
		rot_other = other.matrix.to_quaternion()
		# rot_other = other.matrix.to_quaternion()



		diff = rot_bone.rotation_difference( rot_other )

		# e = bpy.ops.object.empty_add(type='ARROWS', radius=0.3, view_align=False, 
		# 	location=  self.source.pose.bones[bone.name].tail, rotation= (diff.conjugated()).to_euler(),
		# 	layers=(True,) + (False,) * 19)

		self.target.pose.bones[bone.name].rotation_quaternion *= diff.conjugated()

		# self.diffs[bone.name] = diff.copy()

		# try: 
		# 	diff *= self.diffs[bone.parent.name].conjugated()
		# except KeyError:
		# 	pass
		print("{:16} | {} | {}".format(bone.name, diff, diff.angle))

		# 
		# 
		# 
	def debug(self, bone):
		l_bone = self.source.convert_space(pose_bone = bone,
											matrix= bone.matrix,
											from_space="LOCAL",
											to_space="WORLD" )

		lp_bone = self.source.convert_space(pose_bone = bone,
											matrix= bone.matrix,
											from_space="LOCAL_WITH_PARENT",
											to_space="WORLD" )
											
		print("ORIGI== {0:16} | {2:3.0f} | {1}".format(bone.name, bone.rotation_quaternion, degrees(bone.rotation_quaternion.angle)))

		print("LOCAL== {0:16} | {2:3.0f} | {1}".format(bone.name, l_bone.to_quaternion(), degrees(l_bone.to_quaternion().angle)))

		print("PAREN== {0:16} | {2:3.0f} | {1}\n".format(bone.name, lp_bone.to_quaternion(), degrees(lp_bone.to_quaternion().angle)))


	# def set_relative_diff(self, bone):
	# 	b_target = self.target.data.bones[bone.name]

	# 	if b_target.parent is not None:
	# 		global omit
	# 		if not omit:
	# 			print(b_target.parent , " " , b_target, "  ", b_target.parent.diff_quat.conjugated())
	# 		b_target.abs_diff_quat =  b_target.abs_diff_quat * b_target.parent.abs_diff_quat.conjugated()

	# 		b_target.diff_quat = b_target.parent.abs_diff_quat.conjugated() * b_target.abs_diff_quat




	# def get_diff_prop(self, bone):
	# 	global omit
	# 	if not omit:
	# 		print("rot diff: {:16} ".format(bone.name), self.target.data.bones[bone.name].diff_quat)
		
	@staticmethod
	def walk_bones(bone, handler):
		# handler(bone)
		for ch in bone.children:
			# if ch.name == "RightShoulder": omit = False
			handler(ch)
			Armature_converter.walk_bones(ch, handler)

		# omit = False
# walk_bones(get_basebone(source), print_bone)


# def print_bone(b):
# 	if 'cnt' not in print_bone.__dict__:
# 		print_bone.cnt = 0
# 	print_bone.cnt += 1

# 	print(print_bone.cnt, " ", b)


a = Armature_converter('SOURCE','BASE')
a.walk_bones(a.get_basebone(), a.get_abs_diff)
a.set_posemode()
# a.debug(a.get_basebone())
# a.walk_bones(a.get_basebone(), a.debug)
# print("SECONDA PASSATA")
# a.walk_bones(a.get_basebone(), a.set_relative_diff)
# a.walk_bones(a.get_basebone(), a.get_diff_prop)


