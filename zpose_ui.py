import bpy
from os import path
from sys import path as syspath
syspath.append(path.dirname(bpy.data.filepath))
import create_mesh
import imp
imp.reload(create_mesh)
#TODEBUG:
# __import__('code').interact(local={k: v for ns in (globals(), locals()) for k, v in ns.items()})

##########################
# CREATE RNA PROPS
##########################

def on_zp_bone_update(self, context):
    bpy.ops.armature.zpose_verify()

# Assign a collection
class Bone_Collection(bpy.types.PropertyGroup):
    name = bpy.props.StringProperty(name="Source Bone", default="", update=on_zp_bone_update)
    # value = bpy.props.IntProperty(name="Test Prop", default=22)
bpy.utils.register_class(Bone_Collection)

def on_zp_source_update(self, context):
    if context.object.data.zp_source is None or context.object.data.zp_source.type != "ARMATURE" :
        return

    bpy.ops.object.mode_set(mode = 'EDIT')

    context.object.data.zp_source.data.show_names = True
    
    if context.object.data.zp_clearprev:
        for b in context.object.data.edit_bones:
                b.zp_bone.clear()
                b.zp_bone.add()

    if context.object.data.zp_samename:
        bpy.ops.armature.zpose_samename()
    
    bpy.ops.armature.zpose_verify()

# def on_zp_bone_update(self, context):

bpy.types.Armature.zp_source = bpy.props.PointerProperty(name = "Source armature object",
                                description="The Armature from where to get the animations",
                                type=bpy.types.Object, update=on_zp_source_update)

bpy.types.Armature.zp_samename = bpy.props.BoolProperty(name = "Link same-named bones",
                                description = "Create a link to source's bones with the same name",
                                default=True)

bpy.types.Armature.zp_clearprev = bpy.props.BoolProperty(name = "Clear previous linking",
                                description= "When selected any previous linking will be cleared",
                                default=False)

bpy.types.EditBone.zp_bone = bpy.props.CollectionProperty(type=Bone_Collection )
bpy.types.Armature.zp_msg = bpy.props.StringProperty() 

##########################
# PANELS
##########################
class ZP_ArmatureSelectPanel(bpy.types.Panel):
    bl_label = "Convert zero pose"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "data"
    
    @classmethod
    def poll(cls, context):
        return context.object.type == "ARMATURE"

    def draw(self, context):
        ob = context.object
        self.layout.prop(ob.data, "zp_clearprev" )
        self.layout.prop(ob.data, "zp_samename", text="Link same-named bones")

        col = self.layout.column()

        if ob.data.zp_source is None:
            col.alert = True
            col.label(text="Select the source armature to convert from")
            col.prop(ob.data, "zp_source", text="")

        elif ob.data.zp_source.type == "ARMATURE":
            col.alert = False
            col.prop(ob.data, "zp_source", text="")

            box = col.box()
            box.label("Target armature selected,")
            box.label("go to the bone tab to complete the setup:")
            box.operator("wm.properties_context_change", icon='BONE_DATA',
                         text="Go to Bone tab...").context = 'BONE'

class ZP_BoneSelectPanel(bpy.types.Panel):
    bl_label = "Link ZeroPose Bones"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "bone"
    
    @classmethod
    def poll(cls, context):
        return context.object.type == "ARMATURE" 

    def draw(self, context):
        if context.mode == 'EDIT_ARMATURE':
            self.draw_menu(context)
        else:
            self.layout.label(icon='EDITMODE_HLT', text="Enter edit mode to link bones")



    def draw_menu(self, context):
        ob = context.object
        if ob.data.zp_source is None:
            box = self.layout.box()
            box.alert = True  # XXX: this should apply to the box background
            box.label(icon='INFO', text="Select the target Armature in the data tab")
            box.operator("wm.properties_context_change", icon='ARMATURE_DATA',
                         text="Go to Data tab...").context = 'DATA'

            # self.layout.label(text="Select the target Armature in the data context")
        elif ob.data.edit_bones.active:
            self.layout.operator("armature.zpose_verify", icon="FILE_TICK", text="Verify all relations")

            
            self.layout.label(text="Select the source bone(s) for [%s]" % ob.data.edit_bones.active.name)
            row = self.layout.row()
            split = row.split(percentage=0.95)
            col1 = split.column()
            col2 = split.column()

            for i in range(len(ob.data.edit_bones.active.zp_bone)):
                col1.prop_search(ob.data.edit_bones.active.zp_bone[i], "name", 
                                    ob.data.zp_source.data, "bones", text="")

                col2.operator("armature.zpose_removebone", icon="CANCEL", emboss=False, text="").index=i

            self.layout.operator("armature.zpose_addbone", icon="PLUS", text="Add linked bone..")

##########################
# OPERATORS
##########################

class ZP_SameNameLinking(bpy.types.Operator):
    bl_idname = "armature.zpose_samename"
    bl_label = "Create zpose linking by name"

    def execute(self, context):
        ob = context.object
        source = ob.data.zp_source

        if source:
            for b in ob.data.edit_bones:
                if b.name in source.data.bones.keys():
                    b.zp_bone[""].name = b.name

        return {"FINISHED"}

class ZP_VerifyRelations(bpy.types.Operator):
    bl_idname = "armature.zpose_verify"
    bl_label = "Verify armature ZeroPose relations"


    def execute(self, context):
        ob = context.object
        source = ob.data.zp_source
        
        if "fake_bone" in bpy.data.objects.keys():
            custom_bone = bpy.data.objects["fake_bone"] 
        else:
            custom_bone = create_mesh.add_fake_bone(context)

        for pb in source.pose.bones:
            pb.custom_shape = None

        for b in ob.data.edit_bones:
            for i in range(len(b.zp_bone)):
                name = b.zp_bone[i].name
                if name in source.data.bones.keys():
                    # print("set bone ", name)
                    source.pose.bones[name].custom_shape = custom_bone

        return {"FINISHED"}    

class ZP_AddBone(bpy.types.Operator):
    bl_idname = "armature.zpose_addbone"
    bl_label = "Add a linked bone to the Bone_Collection"

    def execute(self, context):
        bone = context.object.data.edit_bones.active
        bone.zp_bone.add()
        return {"FINISHED"}    

class ZP_RemoveBone(bpy.types.Operator):
    bl_idname = "armature.zpose_removebone"
    bl_label = "Remove a linked bone from the Bone_Collection"
    index = bpy.props.IntProperty()

    def execute(self, context):
        bone = context.object.data.edit_bones.active
        bone.zp_bone.remove(self.index)
        bpy.ops.armature.zpose_verify()
        return {"FINISHED"} 


def register():
    bpy.utils.register_module(__name__)
    # for ob in bpy.data.objects:
    #     if ob.type == "ARMATURE":
    #         for b in ob.data.edit_bones:
    #             b.zp_bone.clear()
    #             b.zp_bone.add()

def unregister():
    bpy.utils.unregister_module(__name__)