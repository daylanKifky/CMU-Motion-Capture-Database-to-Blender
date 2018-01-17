import bpy


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

		print("Converting armature {} to {}\n".format(source, target))


	def get_basebone(self):
		basebone = [b for b in self.source.data.bones if b.parent is None]

		if len(basebone) != 1:
			raise Exception("The base armature has to have exactly one base bone")
		else:
			basebone = basebone[0]

		return basebone


	def get_abs_diff(self, bone):
		qbase = self.target.data.bones[bone.name].matrix_local.to_quaternion()
		diff = qbase.rotation_difference( bone.matrix_local.to_quaternion() )

		self.target.data.bones[bone.name].abs_diff_quat = diff 

	def set_relative_diff(self, bone):
		b_target = self.target.data.bones[bone.name]

		if b_target.parent is not None:
			global omit
			if not omit:
				print(b_target.parent , " " , b_target, "  ", b_target.parent.diff_quat.conjugated())
			b_target.abs_diff_quat =  b_target.abs_diff_quat * b_target.parent.abs_diff_quat.conjugated()

			b_target.diff_quat = b_target.parent.abs_diff_quat.conjugated() * b_target.abs_diff_quat




	def get_diff_prop(self, bone):
		global omit
		if not omit:
			print("rot diff: {:16} ".format(bone.name), self.target.data.bones[bone.name].diff_quat)
		
	@staticmethod
	def walk_bones(bone, handler):
		global omit
		for ch in bone.children:
			if ch.name == "RightShoulder": omit = False
			handler(ch)
			Armature_converter.walk_bones(ch, handler)

		omit = False
# walk_bones(get_basebone(source), print_bone)


# def print_bone(b):
# 	if 'cnt' not in print_bone.__dict__:
# 		print_bone.cnt = 0
# 	print_bone.cnt += 1

# 	print(print_bone.cnt, " ", b)


a = Armature_converter('SOURCE','BASE')
a.walk_bones(a.get_basebone(), a.get_abs_diff)
a.walk_bones(a.get_basebone(), a.get_diff_prop)
print("SECONDA PASSATA")
a.walk_bones(a.get_basebone(), a.set_relative_diff)
a.walk_bones(a.get_basebone(), a.get_diff_prop)


