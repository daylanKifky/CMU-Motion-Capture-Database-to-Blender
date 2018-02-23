import bpy

C= bpy.context
D= bpy.data

imported = [a for a in D.objects if a.type == "ARMATURE"] 

if len(imported) == 1:
	imported = imported[0]
	print("Armature found: <{}>".format(imported.name))
else:
	raise Exception("No armature, or more than one found")

bpy.ops.object.armature_add(location=(0,0,0),layers=((False,)+(True,)+(False,)*18))


new = [a for a in D.objects if a.type == "ARMATURE" and a != imported]

if len(new) == 1:
	new = new[0]
	new.name =  imported.name + "_CHORDATA"
	print("Armature Created: <{}>".format(new.name))
else:
	raise Exception("Found more than one newly created armature")

