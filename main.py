import bpy
from mathutils import *
from math import pi
from os import path
from sys import path as syspath
syspath.append(path.dirname(bpy.data.filepath))
import zpose_ui
import convert_armature
from convert_armature import *

# syspath.append("/usr/lib/python3/dist-packages")
# from IPython import embed

import zpose_utils as ZPu
import simplify_armature as ZS

import imp
imp.reload(zpose_ui)
imp.reload(convert_armature)
imp.reload(ZPu)
imp.reload(ZS)

def debug(*args):
    return
    print(" ".join(map(str,args)))

class ZP_call_simplify(bpy.types.Operator):
    bl_idname = "armature.zpose_call"
    bl_label = "ZeroPose call simplify"

    @classmethod
    def poll(cls, context):
        return context.object.type == "ARMATURE" and context.object.data.zp_source

    def invoke(self, context, event):
        self.execute(context)
        return {"FINISHED"}

    def execute(self, context):
        mngr = ZS.ZP_armature_manager(context)
        simplfier = ZS.ZP_simplifier(mngr)
        simplfier.run()

        animator = ZS.ZP_animation_transfer(mngr)
        animator.run()




class ZP_SimplifyArmature(bpy.types.Operator):
    bl_idname = "armature.zpose_simplify"
    bl_label = "ZeroPose convert"
    bl_description = """Create an estimation of the source's animations with other armature's Rest Pose.
    A bone-mapping has to be done from the properties panel before running this operator."""

    range = {"min" : 0, "max" : float("inf")}

    @classmethod
    def poll(cls, context):
        return context.object.type == "ARMATURE" and context.object.data.zp_source

    def invoke(self, context, event):
        self.wm = bpy.context.window_manager
        self.source = context.object.data.zp_source ###
        self.target = context.object ####
        self.frame_initial = context.scene.frame_current
        self.range = {"min" : context.scene.frame_start, "max" : context.scene.frame_end}
        # progress from [0 - 1000]
        tot = len(self.source.animation_data.action.fcurves[0].keyframe_points)
        print("TOTAL OF %d keyframes" % tot)
        print("RANGE", self.range)
         
        self.wm.progress_begin(0, tot)
        # for i in range(tot):
        #     self.wm.progress_update(i)
        #     sleep(0.1)
        # self.wm.progress_end()
        

        self.execute(context)
        return {"FINISHED"}

        

    def execute(self, context):

        # context.window_manager.progress_begin(0, 1)
        # context.window_manager.progress_update(0.5)
        ZPu.clean_empties(["X", "S", "Cube", "Empty"])
        source = self.source = context.object.data.zp_source###
        target = self.target = context.object###
        target.animation_data_clear()###
        target.animation_data_create()###

        # print("response", res)
        # return {'FINISHED'}

        s_rot = ZPu.get_prop_values_at(source, "rotation_quaternion", 0)
        t_rot = ZPu.get_prop_values_at(target, "rotation_quaternion", 0)

        if s_rot != [1,0,0,0] or t_rot != [1,0,0,0]:
            pass 
            # res = bpy.ops.armature.zpose_confirm_rotated('INVOKE_DEFAULT')
        #     self.report({'ERROR'}, "YES!")

        
        debug(" ",  "*"*20, "\n", 
            "Start conversion from {} to {}\n".format(source.name, target.name),
            "*"*20)

        ###~~~
        self.target_basebone = ZPu.get_basebone(self.target.data)
        self.target_init_loc = ZPu.get_prop_values_at(self.target, "location", 0)
        self.target_init_loc = Vector(self.target_init_loc)


        self.source_basebone = ZPu.get_basebone(self.source.data)
        self.source_bbone_init_loc = \
            ZPu.get_prop_values_at(self.source.pose.bones[self.source_basebone], "location", 0)
        self.source_bbone_init_loc = Vector(self.source_bbone_init_loc)


        self.context = context
        ###^^^

        ###~~~
        #keep a copy of source's edit_bones collection
        ZPu.mode_set(self.source, context)
        twopi = 2*pi
        self.source_edit_bones = {}
        for k in source.data.bones.keys():
            editbone = source.data.edit_bones[k]
            editbone.roll = editbone.roll % twopi #this way there are no negative rotations
            self.source_edit_bones[k] = (editbone.name, editbone.roll, editbone.vector.copy())
            # print(k, self.source_edit_bones[k].)


        ZPu.mode_set(self.target, context)
        self.collect_information()
        basebone = target.data.edit_bones[self.target_basebone]
        ###^^^

        debug("Basebone: ",basebone.name)

        ###~~~ created_simplied_zp
        self.source.data.pose_position = "REST"
        self.source.data.update_tag()
        context.scene.update()

        # self.simplify(basebone)
        # self.target.data.update_tag()
        # self.target.update_tag({'OBJECT', 'DATA', 'TIME'})
        # self.context.scene.update()

        ZPu.walk_bones(basebone, self.simplify)
        ###^^^

        self.source.data.pose_position = "POSE"
        ZPu.mode_set(self.target, context, "POSE")
        self.source.data.update_tag()
        context.scene.update()
        debug("***********COPY POSE********")
        basebone = self.target.pose.bones[self.target_basebone]
        self.slerps = {}
        self.copy_pose_bone(basebone)
        self.target.data.update_tag()
        self.target.update_tag({'OBJECT', 'DATA', 'TIME'})
        self.context.scene.update()

        if self.source.animation_data.action:
            self.walk_animation(basebone)
        else:
            self.copy_pose_all(basebone)

        self.wm.progress_end()

        return {"FINISHED"} #end execute(self,context)


    ##########################
    # Second procedure, to be done on every pose in Pose mode
    ##########################

    def set_keyframe_target(self, what = "rotation_quaternion"):
        for b in self.target.pose.bones:
                # print("Setting key to %s"% b.name)
                self.target.keyframe_insert(\
                    'pose.bones["'+ b.name +'"].rotation_quaternion',
                        index=-1, 
                        frame=bpy.context.scene.frame_current, 
                        group=b.name)
        
    
    def walk_animation(self, basebone):
        """Will step on every keyframe of the first fcurve on the source armature. 
        Assumes the keyframes for all the bones are aligned vertically"""
        keyframes = self.source.animation_data.action.fcurves[0].keyframe_points
        for i,keypoint in enumerate(keyframes):
            
            self.context.scene.frame_set(keypoint.co[0])
            if self.context.scene.frame_current < self.range["min"]: continue
            if self.context.scene.frame_current  > self.range["max"]: break

            self.wm.progress_update(i) 

            self.copy_pose_all(basebone)
            self.set_keyframe_target()

            s_basebone = self.source.pose.bones[self.source_basebone]

            #Do Base bone translation
            if self.target.data.zp_roottrans == "BONE":
                basebone.location = s_basebone.location
                self.target.keyframe_insert(\
                    'pose.bones["'+ basebone.name +'"].location',
                        index=-1, 
                        frame=bpy.context.scene.frame_current, 
                        group=basebone.name)

            #Do object translation
            elif self.target.data.zp_roottrans == "OBJECT":
                if not hasattr(self, "target_bbone_init_loc"):
                    self.target_bbone_init_loc = self.target.convert_space(basebone, 
                        Matrix.Translation(basebone.location), "LOCAL", "WORLD")
                
                # D.objects["Empty"].matrix_world = self.target_bbone_init_loc 

                Mw = self.source.convert_space(s_basebone, 
                    Matrix.Translation(s_basebone.location), "LOCAL", "WORLD")
                
                # displacement = basebone.location - self.source_bbone_init_loc
                self.target.location = \
                    self.target_init_loc \
                    - self.target_bbone_init_loc.to_translation() \
                    + self.target_init_loc \
                    + Mw.to_translation()

                self.target.keyframe_insert(\
                    'location',
                        index=-1, 
                        frame=bpy.context.scene.frame_current, 
                        group="location")

        self.context.scene.frame_set(self.frame_initial)

    def copy_pose_all(self, basebone):
        # self.copy_pose_bone(basebone)
        ZPu.walk_bones(basebone, self.copy_pose_bone)


    def copy_pose_bone(self, bone):
        if type(bone) != bpy.types.PoseBone:
            raise TypeError("function expected a bone of type 'PoseBone', not", type(bone))

        zp_bone = self.prev_state[bone.name]["zp_bone"]
        if len(zp_bone) > 1:
            self.pose_multi_bone(bone, zp_bone)
        else:
            self.pose_single_bone(bone, zp_bone)

    def pose_multi_bone(self, bone, other_bones):
        rot_world_space = [o.matrix.copy() for o in other_bones]
        # first_bone = other_bones[0] 
        quat = rot_world_space[0].to_quaternion()

        # for o in other_bones:
        #     self.slerps[o.name] = o.matrix

        # bpy.ops.object.empty_add(location = self.target.matrix_world* other_bones[0]., rotation=empty[1].to_euler(),
        #                 type='ARROWS', radius=0.2)
        self.slerps[bone.name] = self.target.convert_space(bone, 
                                    Matrix(), 
                                    "LOCAL", "WORLD")

        for rot in rot_world_space[1:]:
            # other = self.source.pose.bones[b]
            # first_bone_space.append(self.source.convert_space(first_bone, b.matrix, "POSE", "LOCAL" ))
            # rot_world_space.append( other_bones.matrix.to_quaternion() )
            other = rot.to_quaternion()
            quat = quat.slerp(other, 0.5)

            # quat = quat.slerp(M.to_quaternion(), 0.5)
    
        bone.rotation_quaternion = self.target.convert_space(bone, 
                                    quat.to_matrix().to_4x4(), 
                                    "POSE", "LOCAL").to_quaternion().copy()

        # bpy.app.debug_depsgraph = True
        self.target.data.update_tag()
        # self.context.scene.update()

        self.target.update_tag({'OBJECT', 'DATA', 'TIME'})
        self.context.scene.update()

        # self.target.update_from_editmode()
        # bpy.app.debug_depsgraph = False
        debug("MULTI POSE: %s <---"% bone.name, [a.name for a in other_bones])


    def pose_single_bone(self, bone, other_bones):
        if len(other_bones) == 0 or other_bones[0].name == "":
            debug(bone.name, "No linked bone")
            return
        zp_bname = other_bones[0].name
        bone.rotation_quaternion = self.source.pose.bones[zp_bname].rotation_quaternion

        debug("SINGLE BONE: %s <---"% bone.name, zp_bname)

    ##########################
    # Initial procedure, copy pose in edit mode
    ##########################
    def collect_information(self):
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

    def simplify(self, bone):
        if type(bone) != bpy.types.EditBone:
            raise TypeError("function expected a bone of type 'EditBone', not", type(bone))

        magnitudes = {}
        if len(bone.zp_bone) > 1:
            self.do_multi_bone(bone)
        else:
            self.do_single_bone(bone)

    def do_single_bone(self, bone):
        if len(bone.zp_bone) == 0 or bone.zp_bone[0].name == "":
            debug(bone.name, "No linked bone")
            return

        zp_bname = bone.zp_bone[0].name
        magnitude = self.prev_state[bone.name]["magnitude"]
        
        other = self.source.pose.bones[zp_bname]    

        #Get the direction in WORLD Space
        a = ZPu.bone_vec_to_world(other.head)
        b = ZPu.bone_vec_to_world(other.tail)
        direction = b - a
        
        roll = self.source_edit_bones[zp_bname][1]
        ename = self.source_edit_bones[zp_bname][0]

        if bone.parent:
            Mp = ZPu.get_bone_co_pose_space(self.target.data.bones[bone.parent.name], "tip" )
        else:
            Mp = Matrix()

        Mhead = Matrix.Translation(self.prev_state[bone.name]["head"])
        #D.objects["X"].matrix_world = self.target.matrix_world * Mp #* Mhead 
        bone.head = Mp * self.prev_state[bone.name]["head"]
    
        bone.tail = bone.head + direction.normalized() * magnitude
        bone.roll = roll

        self.target.update_from_editmode()

    def do_multi_bone(self, bone):
        magnitude = self.prev_state[bone.name]["magnitude"]

        others = self.prev_state[bone.name]["zp_bone"]
        # for zp in bone.zp_bone:
        #     others.append(self.source.pose.bones[zp.name])
        # others.sort(key=ZPu.genealogy)

        # assert ZPu.verify_chain(others)
        debug("{:<15}[MULTI] ->{}".format( bone.name, [b.name for b in others]) )

        #Get the direction in WORLD Space
        # a = ZPu.bone_vec_to_world(others[0].head)
        # b = ZPu.bone_vec_to_world(others[-1].tail)
        a = others[0].head
        b = others[-1].tail
        direction = b - a

        if bone.parent:
            Mp = ZPu.get_bone_co_pose_space(self.target.data.bones[bone.parent.name], "tip" )
        else:
            Mp = Matrix()

        Mhead = Matrix.Translation(self.prev_state[bone.name]["head"])
        #D.objects["X"].matrix_world = self.target.matrix_world * Mp #* Mhead 
        bone.head = Mp * self.prev_state[bone.name]["head"]
        bone.tail = bone.head + direction.normalized() * magnitude
        
        #Use average twist, and keep a copy for posterior graphical representation
        # twist = ZPu.get_average_twist(others, direction)
        # self.twists[bone.name] = (bone.head.copy(), twist.copy())
        # bone.roll = twist.angle
        
        bone.roll = ZPu.get_average_roll([self.source_edit_bones[b.name] for b in others], direction)

        self.target.update_from_editmode()
        

        ##########################
        # NOT USED ANYMORE
        ##########################

    # def get_bone_co_pose_space(self, name, tip_or_head):
    #     bone = self.target.data.bones[name]
        
    #     Mtip = Matrix.Translation(bone.tail)
    #     Mhead = Matrix.Translation(bone.head)
        
    #     if tip_or_head.lower() == "tip":
    #         dest = Mtip
    #     elif tip_or_head.lower() == "head":
    #         dest = Mhead
            
    #     if bone.parent:    
    #         Mptip = Matrix.Translation(bone.parent.tail - bone.parent.head)
    #         #head and orientation of parent bone
    #         Mw  = bone.parent.matrix_local
    #         #grandfather orientation
    #         Mw *= bone.parent.matrix.to_4x4().inverted()
    #         #tip of parent bone
    #         Mw *= Mptip
    #         #back to orientation of parent bone
    #         Mw *= bone.parent.matrix.to_4x4()
    #         #tip of bone
    #         Mw *= dest
    #         #orientation of bone
    #         Mw *= bone.matrix.to_4x4()    
    #     else:
    #         Mw = dest
    #         Mw *= bone.matrix.to_4x4()
            
    #     return Mw


    # def mode_set(self, context, who, mode="EDIT"):
    #     debug("Mode set {} of {}".format(mode, who))
    #     bpy.ops.object.mode_set(mode = 'OBJECT')
    #     if mode == "OBJECT": return

    #     if who == self.target or who in ("TARGET", "target", "Target"):
    #         who = self.target
    #         exiting = self.source
    #     elif who == self.source or who in ("SOURCE", "source", "Source"):
    #         who = self.source
    #         exiting =self.target

    #     exiting.select = False
    #     who.select = True
    #     context.scene.objects.active=who
    #     who.data.update_tag()
    #     context.scene.update()
    #     bpy.ops.object.mode_set(mode = mode)
    #     
    

    #end ZP_SimplifyArmature(bpy.types.Operator)




if __name__ == "__main__":
    zpose_ui.register()
    bpy.utils.register_module(__name__)
    #test call
    # bpy.ops.armature.zpose_simplify()
