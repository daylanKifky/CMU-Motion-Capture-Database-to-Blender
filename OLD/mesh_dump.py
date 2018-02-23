import bmesh
import bpy

import json

C = bpy.context
mesh = C.object.data

#Get faces and vertices from the current object
faces = []
for p in mesh.polygons:
    faces.append(tuple([v for v in p.vertices]))
    
verts = [v.co.to_tuple() for v in C.object.data.vertices]


#Dump the geometry data as a json string
json_encoded = json.dumps({"faces": faces, "vertices": verts}, indent=4)

# print(json_encoded)
with open('custom_bone.json', "w") as f:
	f.write(json_encoded)


###########
# Recreate the object as a test

decoded_json = json.loads(json_encoded)
verts_loc = decoded_json["vertices"]
faces = decoded_json["faces"]

mesh = bpy.data.meshes.new("Custom_Shape")
bm = bmesh.new()

for v_co in verts_loc:
    bm.verts.new(v_co)

bm.verts.ensure_lookup_table()

for f_idx in faces:
    bm.faces.new([bm.verts[i] for i in f_idx])

bm.to_mesh(mesh)
mesh.update()

from bpy_extras import object_utils
object_utils.object_data_add(bpy.context, mesh)
ob = C.object

# Add material
mat = bpy.data.materials.new(name="Custom_Shape_material")
ob.data.materials.append(mat)
mat.diffuse_color = (.38, .16, 0.8)