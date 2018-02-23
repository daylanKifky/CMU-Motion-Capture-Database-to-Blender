import bpy
from mathutils import *
from sys import path as syspath
syspath.append(path.dirname(bpy.data.filepath))
import zpose_utils as ZPu

class ZP_armature_manager():
	def __init__(self, context):
		self.context = context
		self.source = context.object.data.zp_source
		self.target = context.object
		self.target.animation_data_clear()
		self.target.animation_data_create()
		self.range = {"min" : context.scene.frame_start, "max" : context.scene.frame_end}
		self.frame_initial = context.scene.frame_current
		
		ZPu.mode_set(self.target, context)

		self.collect_information()

		self.copy_source_edit_bones()
	#end __init__
	
	##########################
	# INITIAL PROCEDURE (info gathering)
	##########################

	def copy_source_edit_bones(self):
		ZPu.mode_set(self.source, self.context)
		twopi = 2*pi
		self.source_edit_bones = {}
		for k in self.source.data.bones.keys():
			editbone = self.source.data.edit_bones[k]
			editbone.roll = editbone.roll % twopi #this way there are no negative rotations
			self.source_edit_bones[k] = (editbone.name, editbone.roll, editbone.vector.copy())
		ZPu.mode_set(self.target, self.context)
		#end copy_source_edit_bones

	def collect_information(self):
		##########################
		# Basebones, and initial displacements
		self.target_basebone = ZPu.get_basebone(self.target.data)
		self.target_init_loc = ZPu.get_prop_values_at(self.target, "location", 0)
		self.target_init_loc = Vector(self.target_init_loc)

		self.source_basebone = ZPu.get_basebone(self.source.data)
		self.source_bbone_init_loc = \
			ZPu.get_prop_values_at(self.source.pose.bones[self.source_basebone], "location", 0)
		self.source_bbone_init_loc = Vector(self.source_bbone_init_loc)
		
		##########################
		# PREV_STATE (bones stuff)
		if self.target.mode != "EDIT":
			ZPu.mode_set(self.target, self.context)
		
		self.prev_state = {}
		for b in self.target.data.bones:
			self.prev_state[b.name] = {
			"head": b.head.copy(), 
			"tail": b.tail.copy(), 
			"magnitude": b.vector.magnitude
			}
			
		for b in self.target.data.edit_bones:
			others = []
			for zp in b.zp_bone:
				others.append(self.source.pose.bones[zp.name])
			others.sort(key=ZPu.genealogy)

			assert ZPu.verify_chain(others)
			self.prev_state[b.name]["zp_bone"] = others
		# end collect_information


class ZP_animation_transfer():
	"""Parse the animation of an armature and copy it to a simpler one.
	Expects the simpler armature with a similar zero pose than the source."""
	def __init__(self, mngr):
		self.mngr = mngr

	def run(self, prog):
		self.mngr.source.data.pose_position = "POSE"
		ZPu.mode_set(self.mngr.target, self.mngr.context, "POSE")
		self.mngr.source.data.update_tag()
		self.mngr.context.scene.update()

		basebone = self.mngr.target.pose.bones[self.mngr.target_basebone]

		if self.mngr.source.animation_data.action:
			self._walk_animation(basebone, prog)
		else:
			self._copy_pose_all(basebone)

		self.mngr.context.scene.frame_set(self.mngr.frame_initial)
		ZPu.mode_set(self.mngr.target, self.mngr.context, "OBJECT")


	def _set_keyframe_target(self, what = "rotation_quaternion"):
		for b in self.mngr.target.pose.bones:
				self.mngr.target.keyframe_insert(\
					'pose.bones["'+ b.name +'"].rotation_quaternion',
						index=-1, 
						frame=bpy.context.scene.frame_current, 
						group=b.name)

	def _walk_animation(self, basebone, prog):
		"""Will step on every keyframe of the first fcurve on the source armature. 
		Assumes the keyframes for all the bones are aligned vertically"""
		keyframes = self.mngr.source.animation_data.action.fcurves[0].keyframe_points
		sc = self.mngr.context.scene
		source = self.mngr.source
		target = self.mngr.target
		total_k = self.mngr.range["max"] - self.mngr.range["min"]
		for i,keypoint in enumerate(keyframes):
			sc.frame_set(keypoint.co[0])
			if sc.frame_current < self.mngr.range["min"]: continue
			if sc.frame_current  > self.mngr.range["max"]: break

			#Set progress indicator on GUI
			prog.iset((sc.frame_current-self.mngr.range["min"] ) / total_k)

			self._copy_pose_all(basebone)
			self._set_keyframe_target()

			s_basebone = source.pose.bones[self.mngr.source_basebone]

			#Do Base bone translation
			if target.data.zp_roottrans == "BONE":
				basebone.location = s_basebone.location
				target.keyframe_insert(\
					'pose.bones["'+ basebone.name +'"].location',
						index=-1, 
						frame=self.mngr.context.scene.frame_current, 
						group=basebone.name)

			#Do object translation
			elif target.data.zp_roottrans == "OBJECT":
				if not hasattr(self.mngr, "target_bbone_init_loc"):
					self.mngr.target_bbone_init_loc = target.convert_space(basebone, 
						Matrix.Translation(basebone.location), "LOCAL", "WORLD")
				
				# D.objects["Empty"].matrix_world = self.target_bbone_init_loc 

				Mw = source.convert_space(s_basebone, 
					Matrix.Translation(s_basebone.location), "LOCAL", "WORLD")
				
				# displacement = basebone.location - self.source_bbone_init_loc
				target.location = \
					self.mngr.target_init_loc \
					- self.mngr.target_bbone_init_loc.to_translation() \
					+ self.mngr.target_init_loc \
					+ Mw.to_translation()

				target.keyframe_insert(\
					'location',
						index=-1, 
						frame=self.mngr.context.scene.frame_current, 
						group="location")

		

	def _copy_pose_all(self, basebone):
	# self._copy_pose_bone(basebone)
		ZPu.walk_bones(basebone, self._copy_pose_bone)

	def _copy_pose_bone(self, bone):
		if type(bone) != bpy.types.PoseBone:
			raise TypeError("function expected a bone of type 'PoseBone', not", type(bone))

		zp_bone = self.mngr.prev_state[bone.name]["zp_bone"]
		if len(zp_bone) > 1:
			self._pose_multi_bone(bone, zp_bone)
		else:
			self._pose_single_bone(bone, zp_bone)

	def _pose_multi_bone(self, bone, other_bones):
		target = self.mngr.target
		rot_world_space = [o.matrix.copy() for o in other_bones]
		# first_bone = other_bones[0] 
		quat = rot_world_space[0].to_quaternion()

		for rot in rot_world_space[1:]:
			other = rot.to_quaternion()
			quat = quat.slerp(other, 0.5)

	
		bone.rotation_quaternion = target.convert_space(bone, 
									quat.to_matrix().to_4x4(), 
									"POSE", "LOCAL").to_quaternion().copy()


		target.data.update_tag()
		target.update_tag({'OBJECT', 'DATA', 'TIME'})
		self.mngr.context.scene.update()

		debug("MULTI POSE: %s <---"% bone.name, [a.name for a in other_bones])

	def _pose_single_bone(self, bone, other_bones):
		if len(other_bones) == 0 or other_bones[0].name == "":
			debug(bone.name, "No linked bone")
			return
		zp_bname = other_bones[0].name
		bone.rotation_quaternion = self.mngr.source.pose.bones[zp_bname].rotation_quaternion

		debug("SINGLE BONE: %s <---"% bone.name, zp_bname)


class ZP_simplifier():
	"""Create an estimation of the base pose of an armature on a simpler one."""
	def __init__(self, mngr):
		self.mngr = mngr

	def run(self):
		basebone = self.mngr.target.data.edit_bones[self.mngr.target_basebone]
		self.mngr.source.data.pose_position = "REST"
		self.mngr.source.data.update_tag()
		self.mngr.context.scene.update()

		ZPu.walk_bones(basebone, self._simplify)

		ZPu.mode_set(self.mngr.target, self.mngr.context, "OBJECT")

	##########################
	# SIMPLIFY
	##########################
	def _simplify(self, bone):
		if type(bone) != bpy.types.EditBone:
			raise TypeError("function expected a bone of type 'EditBone', not", type(bone))

		if len(bone.zp_bone) > 1:
			self._do_multi_bone(bone)
		else:
			self._do_single_bone(bone)

	def _do_single_bone(self, bone):
		if len(bone.zp_bone) == 0 or bone.zp_bone[0].name == "":
			debug(bone.name, "No linked bone")
			return

		zp_bname = bone.zp_bone[0].name
		magnitude = self.mngr.prev_state[bone.name]["magnitude"]
		other = self.mngr.source.pose.bones[zp_bname]	

		#Get the direction in WORLD Space
		a = ZPu.bone_vec_to_world(other.head)
		b = ZPu.bone_vec_to_world(other.tail)
		direction = b - a
		
		roll = self.mngr.source_edit_bones[zp_bname][1]
		ename = self.mngr.source_edit_bones[zp_bname][0]

		if bone.parent:
			Mp = ZPu.get_bone_co_pose_space(self.mngr.target.data.bones[bone.parent.name], "tip" )
		else:
			Mp = Matrix()

		Mhead = Matrix.Translation(self.mngr.prev_state[bone.name]["head"])
		bone.head = Mp * self.mngr.prev_state[bone.name]["head"]
		bone.tail = bone.head + direction.normalized() * magnitude
		bone.roll = roll

		self.mngr.target.update_from_editmode()
	#end _do_single_bone()

	def _do_multi_bone(self, bone):
		magnitude = self.mngr.prev_state[bone.name]["magnitude"]
		others = self.mngr.prev_state[bone.name]["zp_bone"]
		debug("{:<15}[MULTI] ->{}".format( bone.name, [b.name for b in others]) )

		a = others[0].head
		b = others[-1].tail
		direction = b - a

		if bone.parent:
			Mp = ZPu.get_bone_co_pose_space(self.mngr.target.data.bones[bone.parent.name], "tip" )
		else:
			Mp = Matrix()

		Mhead = Matrix.Translation(self.mngr.prev_state[bone.name]["head"])
		bone.head = Mp * self.mngr.prev_state[bone.name]["head"]
		bone.tail = bone.head + direction.normalized() * magnitude
		bone.roll = ZPu.get_average_roll(\
			[self.mngr.source_edit_bones[b.name] for b in others], direction\
			)

		self.mngr.target.update_from_editmode()
	#end _do_multi_bone()


