import bpy
from mathutils import *
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
    return
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
        bpy.ops.object.mode_set(mode = 'EDIT')
        

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
        
        self.source_edit_bones = {}
        for k in source.data.bones.keys():
            editbone = source.data.edit_bones[k]
            self.source_edit_bones[k] = (editbone.name, editbone.roll, editbone.vector.copy())
            # print(k, self.source_edit_bones[k].)


        self.mode_set(context, "Target")
        self.collect_information()
        #TODO: get_basebone interface sucks!
        basebone = Armature_converter.get_basebone(self, "target")
        basebone = target.data.edit_bones[basebone.name]
        debug("Basebone: ",basebone.name)

        Armature_converter.walk_bones(basebone, self.simplify)

        ##########################
        # Create empties, axis and (no well orieted) rotation arcs
        ##########################
        # self.mode_set(context, "Target", "OBJECT")
        # for name, empty in self.twists.items():
        #     bpy.ops.object.empty_add(location = self.target.matrix_world* empty[0], rotation=empty[1].to_euler(),
        #         type='ARROWS', radius=0.2)

        #     # curve_rot = Quaternion((1,0,0,0)) * empty[1].conjugated()
        #     bpy.ops.curve.simple(Simple_Type ="Arc", Simple_startlocation= self.target.matrix_world* empty[0], 
        #         Simple_angle=empty[1].angle, Simple_degrees_or_radians = "Radians", 
        #         Simple_rotation_euler = empty[1].to_euler(), Simple_radius=0.1)

        #     S.create_direction_obj(name, self.target.matrix_world* empty[0], empty[1].axis *0.2)
   

        return {"FINISHED"}

    def collect_information(self):
        self.prev_state = {}
        for b in self.target.data.bones:
             self.prev_state[b.name] = {
             "head": b.head.copy(), 
             "tail": b.tail.copy(), 
             "magnitude": b.vector.magnitude
             }

    def simplify(self, bone):
        magnitudes = {}
        if len(bone.zp_bone) > 1:
            self.do_multi_bone(bone)
        else:
            self.do_single_bone(bone)

    def do_single_bone(self, bone):
        zp_bname = bone.zp_bone[0].name
        magnitude = self.prev_state[bone.name]["magnitude"]
        
        if len(bone.zp_bone) == 0 or zp_bname == "":
            debug(bone.name, "No linked bone")
            return

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
        others = []
        for zp in bone.zp_bone:
            others.append(self.source.pose.bones[zp.name])
        others.sort(key=S.genealogy)

        assert S.verify_chain(others)
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
