import bpy
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
     print(" ".join(map(str,args)))

# __import__('code').interact(local={k: v for ns in (globals(), locals()) for k, v in ns.items()})
# 

class ZP_SimplifyArmature(bpy.types.Operator):
    bl_idname = "armature.zpose_simplify"
    bl_label = "Map the pose in a more complex armature to the currently selected"

    @classmethod
    def poll(cls, context):
        return context.object.type == "ARMATURE" and context.object.data.zp_source

    def invoke(self, context, event):
        self.execute(context)
        return {"FINISHED"}

    def mode_set(self, context, who, mode="EDIT"):
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
        print("****************")
        who.data.update_tag()
        context.scene.update()
        bpy.ops.object.mode_set(mode = 'EDIT')
        

    def execute(self, context):
        source = self.source = context.object.data.zp_source
        target = self.target = context.object

        # __import__('code').interact(local={k: v for ns in (globals(), locals()) for k, v in ns.items()})

        #keep a copy of source's edit_bones collection
        self.mode_set(context, "SOURCE")
        # print(source.data.edit_bones[0])
        
        self.source_edit_bones = {}
        for k in source.data.bones.keys():
            editbone = source.data.edit_bones[k]
            self.source_edit_bones[k] = (editbone.name, editbone.roll)
            # print(k, self.source_edit_bones[k].)


        self.mode_set(context, "Target")
        #TODO: get_basebone interface sucks!
        basebone = Armature_converter.get_basebone(self, "target")
        basebone = target.data.edit_bones[basebone.name]
        print(basebone)

        Armature_converter.walk_bones(basebone, self.simplify)
   

        return {"FINISHED"} 

    def simplify(self, bone):
        magnitudes = {}
        if len(bone.zp_bone) > 1:
            self.do_multi_bone(bone)
        else:
            self.do_single_bone(bone)

    def do_single_bone(self, bone):
        zp_bname = bone.zp_bone[0].name
        magnitude = bone.vector.magnitude
        
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

        bone.tail = bone.head + direction.normalized() * magnitude
        bone.roll = roll

        # print("< {:<12} {:<15}[SINGLE] ->{} | {} | {}".format( ename + " >", bone.name, bone.zp_bone.keys(), direction, roll) )


    def do_multi_bone(bone):
        print("{:<15}[MULTI] ->{}".format( bone.name, bone.zp_bone.keys()) )


if __name__ == "__main__":
    zpose_ui.register()
    bpy.utils.register_module(__name__)
    #test call
    # bpy.ops.armature.zpose_simplify()
