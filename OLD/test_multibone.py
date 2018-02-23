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

# loc = locs[0] + Vector((0,0,1))


a = source.data.bones[1].head_local
b = source.data.bones[2].tail_local

direction = b - a


# Get twist
axis = Vector(quat[1:])
axis.normalize()

ap = axis.project(direction)
print(ap)

twist = Quaternion( (quat.w, ap.x, ap.y, ap.z)  )
twist.normalize()


# Add rotated empty
bpy.ops.object.empty_add(type='ARROWS', radius=0.3, view_align=False, 
							location=  a, rotation= twist.to_euler(),
							layers= (False,) + (True,) + (False,) * 18)


# Draw axis
bpy.ops.object.add(type="MESH", location= a, enter_editmode = True,
						layers= (False,) + (True,) + (False,) * 18)

ob = bpy.context.object

me = ob.data
bm = bmesh.from_edit_mesh(me)

v1 = bm.verts.new((0,0,0))
v2 = bm.verts.new(ap)

bm.edges.new((v1, v2))

bmesh.update_edit_mesh(ob.data)

#put target Bone
bpy.ops.object.mode_set(mode = 'OBJECT')

bpy.ops.object.select_all(action = "DESELECT")
target.select = True
bpy.context.scene.objects.active = target
magnitude = the_bone.vector.magnitude
bpy.ops.object.mode_set(mode = 'EDIT')

the_bone = target.data.edit_bones["the_bone"]

the_bone.tail = the_bone.head + direction.normalized() * magnitude
the_bone.roll = twist.angle






# /**
#    Decompose the rotation on to 2 parts.
#    1. Twist - rotation around the "direction" vector
#    2. Swing - rotation around axis that is perpendicular to "direction" vector
#    The rotation can be composed back by 
#    rotation = swing * twist

#    has singularity in case of swing_rotation close to 180 degrees rotation.
#    if the input quaternion is of non-unit length, the outputs are non-unit as well
#    otherwise, outputs are both unit
# */
# inline void swing_twist_decomposition( const xxquaternion& rotation,
#                                        const vector3&      direction,
#                                        xxquaternion&       swing,
#                                        xxquaternion&       twist)
# {
#     vector3 ra( rotation.x, rotation.y, rotation.z ); // rotation axis
#     vector3 p = projection( ra, direction ); // return projection v1 on to v2  (parallel component)
#     twist.set( p.x, p.y, p.z, rotation.w );
#     twist.normalize();
#     swing = rotation * twist.conjugated();
# }





def swing_twist_decomp(quat, axis):
    """Perform a Swing*Twist decomposition of a Quaternion. This splits the
    quaternion in two: one containing the rotation around axis (Twist), the
    other containing the rotation around a vector parallel to axis (Swing).
    Returns two quaternions: Swing, Twist.
    """

    # Current rotation axis
    ra = quat.q[1:]
    # Ensure that axis is normalised
    axis_norm = axis/np.linalg.norm(axis)
    # Projection of ra along the given axis
    p = np.dot(ra, axis_norm)*axis_norm
    # Create Twist
    qin = [quat.q[0], p[0], p[1], p[2]]
    twist = Quaternion(qin/np.linalg.norm(qin))
    # And Swing
    swing = quat*twist.conjugate()

    return swing, twist


