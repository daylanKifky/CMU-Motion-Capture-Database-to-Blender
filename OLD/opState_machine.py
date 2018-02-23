import bpy
from mathutils import *
from math import pi

from time import sleep


# 'DEBUG', 'INFO', 'OPERATOR', 'PROPERTY', 'WARNING', 'ERROR', 'ERROR_INVALID_INPUT', 'ERROR_INVALID_CONTEXT', 'ERROR_OUT_OF_MEMORY'


class initOperator(bpy.types.Operator):
    """Begin the execution"""
    bl_idname = "states.init"
    bl_label = "INIT STATE MACHINE"
    bl_options = {'REGISTER'}#{'REGISTER', 'INTERNAL'}

    num = bpy.props.IntProperty(name = "Counter",
                                    description="tocount :)",
                                    default = 1)

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        print("INIT EXEC")
        # self.report({'WARNING'}, "Applying zpose conversion on rotated armatures")
        return {'FINISHED'}

    def invoke(self, context, event):
        print("INIT INVOKE")
        self.num = 4
        self.report({'INFO'}, "INIT CALL")
        sleep(0.5)
        bpy.ops.states.repeat("INVOKE_DEFAULT")
        return {'FINISHED'} 

class repeaterOperator(bpy.types.Operator):
    """Begin the execution"""
    bl_idname = "states.repeat"
    bl_label = "REPEAT STATE MACHINE"
    bl_options = {'REGISTER'}#{'REGISTER', 'INTERNAL'}


    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        print("INIT EXEC")
        # self.report({'WARNING'}, "Applying zpose conversion on rotated armatures")
        return {'FINISHED'}

    def invoke(self, context, event):
        init_props = bpy.ops.states.init.get_rna()
        self.report({'INFO'}, "REPEATER CALL # %d" % init_props.num)
        print("REPEAT INVOKE" , init_props.num)
        init_props.num -=8
        sleep(0.5)
        return {'FINISHED'}      




class SimpleConfirmOperator(bpy.types.Operator):
    """Really?"""
    bl_idname = "armature.zpose_confirm_rotated"
    bl_label = "This operator doesn't work well on rotated armatures, continue anyway?"
    bl_options = {'REGISTER'}#{'REGISTER', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        # self.report({'WARNING'}, "Applying zpose conversion on rotated armatures")
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = bpy.context.window_manager

        # progress from [0 - 1000]
        tot = 1000
        wm.progress_begin(0, tot)
        for i in range(tot):
            wm.progress_update(i)
            sleep(0.001)
        wm.progress_end()
        bpy.ops.armature.zpose_repeat('INVOKE_DEFAULT')
        # return {"FINISHED"}
        return context.window_manager.invoke_confirm(self, event)

class repeatOperator(bpy.types.Operator):
    """Really?"""
    bl_idname = "armature.zpose_repeat"
    bl_label = "repeat_call"
    bl_options = {'REGISTER'}#{'REGISTER', 'INTERNAL'}

    num = 0

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        self.report({'INFO'}, "call # %d"% self.num)
        return {'FINISHED'}

    def invoke(self, context, event):
        print("invoke repeat, number:", self.num)
        self.report({'INFO'}, "call # %d"% self.num)
        if self.num < 3:
            self.num += 1
            bpy.ops.armature.zpose_confirm_rotated('INVOKE_DEFAULT')
        return context.window_manager.invoke_confirm(self, event)



if __name__ == "__main__":
    # zpose_ui.register()
    bpy.utils.register_module(__name__)
    #test call
    # bpy.ops.armature.zpose_simplify()
