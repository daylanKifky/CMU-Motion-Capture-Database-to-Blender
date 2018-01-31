import bpy, bmesh
from mathutils import *

D = bpy.data

def clean_empties():
	for ob in D.scenes['Scene'].objects:
			if ob.type == "EMPTY" or ob.type == "MESH":
				D.scenes['Scene'].objects.unlink(ob)

# Assign a collection
class BoneList(bpy.types.PropertyGroup):
    name = bpy.props.StringProperty(name="other_bone", default="")
    # value = bpy.props.IntProperty(name="Test Prop", default=22)

bpy.utils.register_class(BoneList)

bpy.types.Bone.others = \
    bpy.props.CollectionProperty(type=BoneList)


source = D.objects["SOURCE"]
target = D.objects["TARGET"]
bpy.ops.object.mode_set(mode = 'OBJECT')

the_bone = target.data.bones["the_bone"]

target.data.bones['the_bone'].others.clear()

target.data.bones['the_bone'].others.add()
target.data.bones['the_bone'].others[-1].name = "Bone.001"

target.data.bones['the_bone'].others.add()
target.data.bones['the_bone'].others[-1].name = "Bone.002"

names = [source.data.bones[k].name for k in the_bone.others.keys()]

quats = [source.data.bones[k].matrix.to_quaternion() for k in the_bone.others.keys()]

quats_local = [source.data.bones[k].matrix_local.to_quaternion() for k in the_bone.others.keys()]

locs = [source.data.bones[k].head_local for k in the_bone.others.keys()]


print(quats)
print(names)

clean_empties()

# INITIAL SLERP
q = Quaternion()
q.identity()


# SEQUENTIAL SLERP

quat = quats_local[0].slerp(quats_local[1],0.5)

loc = locs[0] + Vector((0,0,1))


a = source.data.bones[1].head_local
b = source.data.bones[2].tail_local

c = b - a

for i in range(4):
	bpy.ops.object.mode_set(mode = 'OBJECT')
	d = c * i/4
	loc = a + d
	quat = quats_local[0].slerp(quats_local[1],i/4)


	bpy.ops.object.empty_add(type='ARROWS', radius=0.3, view_align=False, 
							location=  loc, rotation= quat.to_euler(),
							layers= (False,) + (True,) + (False,) * 18)

	direction, rot = quat.to_axis_angle()

	bpy.ops.object.add(type="MESH", location= loc, enter_editmode = True,
						layers= (False,) + (True,) + (False,) * 18)

	ob = bpy.context.object

	me = ob.data
	bm = bmesh.from_edit_mesh(me)

	v1 = bm.verts.new((0,0,0))
	v2 = bm.verts.new(direction)

	bm.edges.new((v1, v2))

	bmesh.update_edit_mesh(ob.data)
	

bpy.ops.object.mode_set(mode = 'OBJECT')
d = c 
loc = a + d
quat = quats_local[0].slerp(quats_local[1],1)


bpy.ops.object.empty_add(type='ARROWS', radius=0.3, view_align=False, 
						location=  loc, rotation= quat.to_euler(),
						layers= (False,) + (True,) + (False,) * 18)
	



# a.name for a in C.object.data.bones['the_bone'].others]


