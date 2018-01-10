import bpy
import os
from os import walk
from os.path import splitext
import csv


C= bpy.context
D= bpy.data

print("BATCH IMPORT")

IMPORT_MAX = 2

def clean_scene():
	for a in D.actions:
		D.actions.remove(a)

	for a in D.armatures:
		D.armatures.remove(a)

	for a in D.objects:
		D.objects.remove(a)


data_dir = os.path.join(os.path.dirname(bpy.data.filepath), "raw_data")

files = {}
for (dirpath, dirnames, filenames) in walk(data_dir):
	files[dirpath] = [name for name in filenames if splitext(name)[1] == ".bvh"]


print(files)

with open(os.path.join(data_dir,'bones.csv'), 'w', newline='') as csvfile:
	spamwriter = csv.writer(csvfile, delimiter=',',
							quotechar='|', quoting=csv.QUOTE_MINIMAL)
	i = 0
	for directory in files:
		print("Checking: ", directory)

		for f in files[directory]:
			clean_scene()
			bpy.ops.import_anim.bvh(filepath=directory + "/" + f, axis_forward='-Z', axis_up='Y', 
			filter_glob="*.bvh", target='ARMATURE', global_scale=0.2, frame_start=1, 
			use_fps_scale=True, update_scene_fps=True, update_scene_duration=True, use_cyclic=False, rotate_mode='QUATERNION')
			
			if C.object.name != splitext(f)[0]:
				print("WRONG NAMED ARMATURE")
				spamwriter.writerow([C.object.name] + ["WRONG NAMED ARMATURE"])

			else:
				print("ARMATURE: ", C.object.name)
				# print([a.name for a in C.object.data.bones])
				spamwriter.writerow([C.object.name] + [a.name for a in C.object.data.bones])

			i+=1
			if i >= IMPORT_MAX: break

		if i >= IMPORT_MAX: break


