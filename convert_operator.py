import bpy
from os import path
from sys import path as syspath
syspath.append(path.dirname(bpy.data.filepath))
import convert_armature as Z


class ToolsPanel(bpy.types.Panel):
    bl_label = "Convert zero pose"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "Zero Pose"
    bpy.types.Scene.pippo = bpy.props.PointerProperty(type=bpy.types.Object)
    bpy.types.Scene.bone = bpy.props.StringProperty()
 
    def draw(self, context):
        ob = context.object
        self.layout.operator("usless.test")
        self.layout.label(text="Some object:")
        sc = bpy.data.scenes['Scene']
        self.layout.prop(sc, "pippo", text="")
        if sc.pippo:
            if sc.pippo.type == 'ARMATURE':
                self.layout.label(text="Bone:")
                self.layout.prop_search(sc, "bone", sc.pippo.data, "bones", text="")
        
        self.layout.prop(ob, "name", text="")


class ArmatureConvertOperator(bpy.types.Operator):
	bl_idname = "armature.convert_zeropose"
	bl_label = "Convert armature zeropose"


	def execute(self, context):
		Z.main()
		return {'FINISHED'}



def register():
	bpy.utils.register_class(ArmatureConvertOperator)

def unregister():
	bpy.utils.unregister_class(ArmatureConvertOperator)


if __name__ == "__main__":
	register()
