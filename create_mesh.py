import bmesh
import bpy
from mathutils import Color
from os import path
from sys import exit

from os import path
from sys import path as syspath
syspath.append(path.dirname(bpy.data.filepath))

import json

import zpose_utils as ZPu
import imp
imp.reload(ZPu)

C = bpy.context
D = bpy.data

remove_fake_from_scene = False

palette={"0xe41a1c","0x377eb8","0x4daf4a","0x984ea3",
"0xff7f00","0xffff33","0xa65628","0xf781bf","0x999999"}

# palette = {"000000"}

def set_active(context, ob):
	bpy.ops.object.mode_set(mode = 'OBJECT')
	bpy.ops.object.select_all(action="DESELECT")
	ob.select = True
	context.scene.objects.active = ob

def hex_to_rgb(color_str):
    # supports '123456', '#123456' and '0x123456'
    (r,g,b)= map(lambda component: component / 255, bytes.fromhex(color_str[-6:]))
    return (r,g,b)

mat_sufix = "_zp_material"
prefix = "zp_fake_bone_"

def add_fake_bone(context = bpy.context, filename='custom_bone.json', 
					location=None, color=(1, .16, 0),
					layers =  (False,) * 19 + (True,),
					name = prefix, mat=None ):
	
	print(name, color)

	prev_ob = context.object
	ZPu.mode_set(prev_ob, context, mode="OBJECT")

	#TODO: change to the script location
	filename = path.join(path.dirname(bpy.data.filepath),filename)

	#Create or get mesh
	if "%smesh"%prefix in D.meshes.keys():
		mesh = D.meshes["%smesh"%prefix]

	else:
		with open(filename, "r") as f:
			json_readed = f.read()
		
		decoded_json = json.loads(json_readed)
		verts_loc = decoded_json["vertices"]
		faces = decoded_json["faces"]

		mesh = bpy.data.meshes.new("%s_mesh"%prefix)
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
	ob = object_utils.object_data_add(bpy.context, mesh, name=name)
	ob = ob.object
	ob.layers = layers

	if location:
		ob.location = location
	
	if not mat:
		if type(color) not in [tuple, list, Color]: 
			mat_name = color + mat_sufix
			color = hex_to_rgb(color)
		else:
			mat_name = "lala" + tuple(color) + mat_sufix

		if mat_name in bpy.data.materials:
			mat = bpy.data.materials[mat_name]
		else:	
			mat = bpy.data.materials.new(name= mat_name)
			mat.diffuse_color = color


	if len(ob.material_slots) < 1:
		override = context.copy()
		override["object"] =  ob
		bpy.ops.object.material_slot_add(override)
	

	ob.material_slots[0].link = "OBJECT"
	ob.material_slots[0].material = mat

	if remove_fake_from_scene:
		ob.use_fake_user = True
		context.scene.objects.unlink(ob)

	ZPu.mode_set(prev_ob, context, mode="EDIT")
	return ob

	# set_active(context, prev_ob)
	# bpy.ops.object.mode_set(mode = 'EDIT')


# def add_colored_bone(name):
# 	context = bpy.context
# 	mats = [k for k in bpy.data.materials.keys() if k.endswith(mat_sufix)]
# 	mat = None
# 	c = None
# 	try:
# 		c = palette.pop()
# 		while c + mat_sufix in mats:
# 			c = palette.pop()	

# 	except KeyError as e:
# 		mat = bpy.data.materials[choice(mats)]


# 	return add_fake_bone(context, name=name, color = c, mat = mat)

import pdb

from random import choice
def add_colored_bone(bone_name):
	context = bpy.context
	mats = [k for k in bpy.data.materials.keys() if k.endswith(mat_sufix)]
	material = None
	c = None

	# pdb.set_trace()
	if palette:
		c = palette.pop()
		while palette and c+mat_sufix in mats:
			c = palette.pop()
	else:	
		material = bpy.data.materials[choice(mats)]
		print (material)



	return add_fake_bone(context, name=bone_name, color=c, mat=material)

	# add_fake_bone(context, name=name, color = c, mat = mat)	

	# print("ADD COLORED BONE!")

if __name__ == '__main__':
	add_colored_bone("fake")


