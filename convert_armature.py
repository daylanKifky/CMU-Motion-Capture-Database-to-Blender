import bpy
from math import degrees
from mathutils import Quaternion


C= bpy.context
D= bpy.data

def clean_empties():
	for ob in D.scenes['Scene'].objects:
			if ob.type == "EMPTY":
				D.scenes['Scene'].objects.unlink(ob)



class Armature_converter:
	"""Translates the animation of one armature to another with different zero pose"""
	bpy.types.Bone.diff_quat = bpy.props.FloatVectorProperty(
			"Difference rotation", 
			subtype= "QUATERNION", 
			size = 4, 
			default=(1,0,0,0))

	bpy.types.Bone.diff_vec = bpy.props.FloatVectorProperty(
			"Difference position", 
			subtype= "TRANSLATION", 
			size = 3, 
			default=(0,0,0))
	
	def __init__(self, source, target):
		self.source = D.objects[source]
		self.target = D.objects[target]
		self.root_translation = True
		self.inherit_rotations = True
		self.range = {"min" : 0, "max" : float("inf")}

		self.set_poseposition("REST")

		C.scene.objects.active = self.target
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
		self.get_basebone("target").rotation_quaternion.identity()
		self.walk_bones(self.get_basebone("target"), lambda b: b.rotation_quaternion.identity())

	def get_pose_diff(self):
		if not self.inherit_rotations:
			for b in self.target.data.bones:
				b.use_inherit_rotation = False
			return
		
		for b in self.target.data.bones:
			b.use_inherit_rotation = True 

		self.reset_pose()
		self.walk_bones(self.get_basebone(), self.get_bone_diff)

		
	def get_bone_diff(self, bone):
		rot_bone =  bone.matrix.to_quaternion() 
		other = self.target.data.bones[bone.name]
		rot_other = other.matrix.to_quaternion()

		bone.diff_quat = rot_bone.rotation_difference( rot_other )

	def set_bone_from_diff(self, bone):
		t_bone = self.target.pose \
					.bones[bone.name]

		C.scene.objects.active = self.target
		bpy.ops.object.mode_set(mode = 'POSE')

		###
		if self.root_translation:
			v = self.source.pose.bones[bone.name].location
		else:
			v = (0,0,0)

		self.target.pose \
				.bones[bone.name] \
				.location = v

		###
		if not self.inherit_rotations:
			self.set_poseposition()
			# bpy.ops.object.mode_set(mode = 'OBJECT')		
			# e = bpy.ops.object.empty_add(type='ARROWS', radius=0.3, view_align=False, 
			# 			location=  self.source.pose.bones[bone.name].tail, rotation= self.source.pose.bones[bone.name].matrix.to_euler(),
			# 			layers=(True,) + (False,) * 19)

			m = self.source.pose.bones[bone.name].matrix.copy()
			m.resize_4x4()
			t_bone.matrix = m

			# bpy.ops.object.select_all(action = 'DESELECT')
			# self.target.select = True
			
								
			return

		###
		t_bone.rotation_quaternion *= bone.diff_quat.conjugated() \
										* self.source.pose.bones[bone.name].rotation_quaternion

		# print("{:16} | {} | {}".format(bone.name, bone.diff_quat, bone.diff_quat))
	
	def set_pose_from_diff(self):
		self.reset_pose()
		self.set_bone_from_diff(self.get_basebone())
		self.walk_bones(self.get_basebone(), self.set_bone_from_diff)
	
	@staticmethod
	def walk_bones(bone, handler):
		for ch in bone.children:
			handler(ch)
			Armature_converter.walk_bones(ch, handler)

	def convert_animation(self):
		name = self.get_basebone("target").name
		
		keyframes = self.source.animation_data.action.fcurves[0].keyframe_points
		for i,keypoint in enumerate(keyframes):
			if i < self.range["min"]: continue
			if i > self.range["max"]: break

			C.scene.frame_set(keypoint.co[0])
			self.set_pose_from_diff()
			
			if self.root_translation:
				self.target.keyframe_insert(\
					'pose.bones["'+ name +'"].location',
						index=-1, 
						frame=bpy.context.scene.frame_current, 
						group=name)

			for b in self.target.pose.bones:
				# print("Setting key to %s"% b.name)
				self.target.keyframe_insert(\
					'pose.bones["'+ b.name +'"].rotation_quaternion',
						index=-1, 
						frame=bpy.context.scene.frame_current, 
						group=b.name)

		print("Done")


def main():
	# Don't ee all operators in info window
	bpy.app.debug_wm = False
	clean_empties()

	a = Armature_converter('SOURCE','TARGET')
	a.range["max"] = 20
	a.root_translation = True
	a.inherit_rotations = True
	a.get_pose_diff()

	a.convert_animation()
	# a.set_pose_from_diff()
	a.set_poseposition()

	# See all operators in info window
	bpy.app.debug_wm = True

	# e = bpy.ops.object.empty_add(type='ARROWS', radius=0.3, view_align=False, 
			# 	location=  self.source.pose.bones[bone.name].tail, rotation= (diff.conjugated()).to_euler(),
			# 	layers=(True,) + (False,) * 19)
	
if __name__ == '__main__':
	main()
