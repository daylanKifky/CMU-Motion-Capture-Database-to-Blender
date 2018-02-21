import bpy
from mathutils import *
from math import pi
from os import path
from sys import path as syspath
syspath.append(path.dirname(bpy.data.filepath))
import zpose_ui
import convert_armature
from convert_armature import *

import simplify_armature as S


import imp
imp.reload(zpose_ui)
imp.reload(convert_armature)
imp.reload(S)

def debug(*args):
    # return
    print(" ".join(map(str,args)))

# __import__('code').interact(local={k: v for ns in (globals(), locals()) for k, v in ns.items()})
# 

class ZP_SimplifyArmature(bpy.types.Operator):
    bl_idname = "armature.zpose_simplify"
    bl_label = "Map the pose in a more complex armature to the currently selected"

    twists = {}

    @classmethod
    def poll(cls, context):
        return context.object.type == "ARMATURE" and context.object.data.zp_source

    def invoke(self, context, event):
        self.execute(context)
        return {"FINISHED"}

    def mode_set(self, context, who, mode="EDIT"):
        debug("Mode set {} of {}".format(mode, who))
        bpy.ops.object.mode_set(mode = 'OBJECT')
        if mode == "OBJECT": return

        if who == self.target or who in ("TARGET", "target", "Target"):
            who = self.target
            exiting = self.source
        elif who == self.source or who in ("SOURCE", "source", "Source"):
            who = self.source
            exiting =self.target

        exiting.select = False
        who.select = True
        context.scene.objects.active=who
        who.data.update_tag()
        context.scene.update()
        bpy.ops.object.mode_set(mode = mode)
        

    def execute(self, context):
        S.clean_empties(["X", "S", "Cube"])
        source = self.source = context.object.data.zp_source
        target = self.target = context.object
        
        debug(" ",  "*"*20, "\n", 
            "Start conversion from {} to {}\n".format(source.name, target.name),
            "*"*20)

        self.context = context
        # __import__('code').interact(local={k: v for ns in (globals(), locals()) for k, v in ns.items()})

        #keep a copy of source's edit_bones collection
        self.mode_set(context, "SOURCE")
        # print(source.data.edit_bones[0])
        
        twopi = 2*pi
        self.source_edit_bones = {}
        for k in source.data.bones.keys():
            editbone = source.data.edit_bones[k]
            editbone.roll = editbone.roll % twopi #this way there are no negative rotations
            self.source_edit_bones[k] = (editbone.name, editbone.roll, editbone.vector.copy())
            # print(k, self.source_edit_bones[k].)


        self.mode_set(context, "Target")
        self.collect_information()
        #TODO: get_basebone interface sucks!
        basebone = Armature_converter.get_basebone(self, "target")
        basebone = target.data.edit_bones[basebone.name]
        debug("Basebone: ",basebone.name)

        self.source.data.pose_position = "REST"
        self.source.data.update_tag()
        context.scene.update()

        Armature_converter.walk_bones(basebone, self.simplify)

        self.source.data.pose_position = "POSE"
        self.mode_set(context, "TARGET", "POSE")
        self.source.data.update_tag()
        context.scene.update()
        debug("***********COPY POSE********")
        basebone = Armature_converter.get_basebone(self, "target")
        self.slerps = {}
        Armature_converter.walk_bones(basebone, self.copy_pose)

        ##########################
        # Create empties, axis and (no well orieted) rotation arcs
        ##########################
        self.mode_set(context, "Target", "OBJECT")
        # for name, rot in self.slerps.items():
        #     bpy.ops.object.empty_add(
        #         location = self.target.matrix_world* self.target.pose.bones[name].matrix.to_translation(), 
        #         rotation=rot.to_euler(),
        #         type='ARROWS', radius=0.2)

        for name, m in self.slerps.items():
            bpy.ops.object.empty_add(
                location = m.to_translation(), 
                rotation=m.to_euler(),
                type='ARROWS', radius=0.2)


        # for name, empty in self.twists.items():
        #     bpy.ops.object.empty_add(location = self.target.matrix_world* empty[0], rotation=empty[1].to_euler(),
        #         type='ARROWS', radius=0.2)

        #     # curve_rot = Quaternion((1,0,0,0)) * empty[1].conjugated()
        #     bpy.ops.curve.simple(Simple_Type ="Arc", Simple_startlocation= self.target.matrix_world* empty[0], 
        #         Simple_angle=empty[1].angle, Simple_degrees_or_radians = "Radians", 
        #         Simple_rotation_euler = empty[1].to_euler(), Simple_radius=0.1)

        #     S.create_direction_obj(name, self.target.matrix_world* empty[0], empty[1].axis *0.2)
   

        return {"FINISHED"}
    ##########################
    # Second procedure, to be done on every pose in Pose mode
    ##########################

    def copy_pose(self, bone):
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

        print("="*10, bone.rotation_quaternion.copy())

        bpy.app.debug_depsgraph = True
        self.target.data.update_tag()
        # self.context.scene.update()

        self.target.update_tag({'OBJECT', 'DATA', 'TIME'})
        self.context.scene.update()

        # self.target.update_from_editmode()
        bpy.app.debug_depsgraph = False
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
            others.sort(key=S.genealogy)

            assert S.verify_chain(others)

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
        a = S.bone_vec_to_world(other.head)
        b = S.bone_vec_to_world(other.tail)
        direction = b - a
        
        roll = self.source_edit_bones[zp_bname][1]
        ename = self.source_edit_bones[zp_bname][0]

        Mp = self.get_bone_co_pose_space(bone.parent.name, "tip" )
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
        # others.sort(key=S.genealogy)

        # assert S.verify_chain(others)
        debug("{:<15}[MULTI] ->{}".format( bone.name, [b.name for b in others]) )

        #Get the direction in WORLD Space
        # a = S.bone_vec_to_world(others[0].head)
        # b = S.bone_vec_to_world(others[-1].tail)
        a = others[0].head
        b = others[-1].tail
        direction = b - a

        Mp = self.get_bone_co_pose_space(bone.parent.name, "tip" )
        Mhead = Matrix.Translation(self.prev_state[bone.name]["head"])
        #D.objects["X"].matrix_world = self.target.matrix_world * Mp #* Mhead 
        bone.head = Mp * self.prev_state[bone.name]["head"]
        bone.tail = bone.head + direction.normalized() * magnitude
        
        #Use average twist, and keep a copy for posterior graphical representation
        # twist = S.get_average_twist(others, direction)
        # self.twists[bone.name] = (bone.head.copy(), twist.copy())
        # bone.roll = twist.angle
        
        bone.roll = S.get_average_roll([self.source_edit_bones[b.name] for b in others], direction)

        self.target.update_from_editmode()
        

    def get_bone_co_pose_space(self, name, tip_or_head):
        bone = self.target.data.bones[name]
        
        Mtip = Matrix.Translation(bone.tail)
        Mhead = Matrix.Translation(bone.head)
        
        if tip_or_head.lower() == "tip":
            dest = Mtip
        elif tip_or_head.lower() == "head":
            dest = Mhead
            
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




if __name__ == "__main__":
    zpose_ui.register()
    bpy.utils.register_module(__name__)
    #test call
    # bpy.ops.armature.zpose_simplify()
