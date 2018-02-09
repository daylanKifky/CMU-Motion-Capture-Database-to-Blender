import bmesh
import bpy
from mathutils import Color
from os import path
from sys import exit

import json

C = bpy.context
D = bpy.data

def set_active(context, ob):
	bpy.ops.object.mode_set(mode = 'OBJECT')
	bpy.ops.object.select_all(action="DESELECT")
	ob.select = True
	context.scene.objects.active = ob

def hex_to_rgb(color_str):
    # supports '123456', '#123456' and '0x123456'
    (r,g,b)= map(lambda component: component / 255, bytes.fromhex(color_str[-6:]))
    return (r,g,b)

def add_fake_bone(context = bpy.context, filename='custom_bone.json', 
					location=None, color=(1, .16, 0),
					layers =  (False,) * 19 + (True,) ):
	
	prev_ob = C.object
	bpy.ops.object.mode_set(mode = 'OBJECT')
	#TODO: change to the script location
	filename = path.join(path.dirname(bpy.data.filepath),filename)

	#Create or get mesh
	if "fake_bone_mesh" in D.meshes.keys():
		mesh = D.meshes["fake_bone_mesh"]

	else:
		with open(filename, "r") as f:
			json_readed = f.read()
		
		decoded_json = json.loads(json_readed)
		verts_loc = decoded_json["vertices"]
		faces = decoded_json["faces"]

		mesh = bpy.data.meshes.new("fake_bone_mesh")
		bm = bmesh.new()

		for v_co in verts_loc:
		    bm.verts.new(v_co)

		bm.verts.ensure_lookup_table()

		for f_idx in faces:
		    bm.faces.new([bm.verts[i] for i in f_idx])

		bm.to_mesh(mesh)
		mesh.update()

	#Create Object
	from bpy_extras import object_utils
	ob = object_utils.object_data_add(bpy.context, mesh, name="fake_bone")
	ob = ob.object
	ob.layers = layers

	if location:
		ob.location = location
	
	mat = bpy.data.materials.new(name="fake_bone_material")
	if len(ob.material_slots) < 1:
		override = context.copy()
		override["object"] =  ob
		bpy.ops.object.material_slot_add(override)
	
	ob.material_slots[0].link = "OBJECT"
	ob.material_slots[0].material = mat

	if type(color) in [tuple, list, Color]: 
		mat.diffuse_color = color
	else:
		mat.diffuse_color = hex_to_rgb(color)

	set_active(context, prev_ob)
	bpy.ops.object.mode_set(mode = 'EDIT')

 


def create_mat(color):
	mat = bpy.data.materials.new(name="fake_bone_material")
	if type(color) in [tuple, list, Color]: 
		mat.diffuse_color = color
	else:
		mat.diffuse_color = hex_to_rgb(color)

	return mat


if __name__ == '__main__':
	add_fake_bone()