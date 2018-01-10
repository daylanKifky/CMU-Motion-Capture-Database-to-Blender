from sys import path as syspath
import bpy
import math
from mathutils import *
syspath.append('/home/mrkifky/.local/lib/python3.5/site-packages')
from sklearn.neighbors import NearestNeighbors
import numpy as np

D= bpy.data

sce = bpy.context.scene
ob = D.objects['ArmatureBase']

values = []

for f in range(int(ob.animation_data.action.frame_range[0]), int(ob.animation_data.action.frame_range[1])):
    sce.frame_set(f)
    # print("Frame %i" % f)
    pose = []
    for pbone in ob.pose.bones:
        for i in range(4):
        	pose.append(pbone.rotation_quaternion[i])

    values.append(pose)
    # print(pbone.name, pbone.rotation_quaternion)

poses = np.array(values)

print("Array created, lenght {}, \n first element lenght:  {} ".format(
	len(poses),
	len(poses[0])))
print(poses)


sce.frame_set(82)
target = D.objects['ArmatureTarget']
targetvalues = []
for pbone in target.pose.bones:
	if pbone.name == "Bone1":
		continue
	for i in range(4):
		targetvalues.append(pbone.rotation_quaternion[i])

targetvalues = targetvalues[:4] + [0,0,0,0] + targetvalues[4:]

targetpose = np.array(targetvalues)

print("Target array created, length: ", len(targetpose))
print("*"*20, "\n")

clamp = lambda n: max(min(1, n), -1)

def alpha_quats(q1, q2):
    # if q1.dot(q2) < 0:
    #     q2 = -q2
    q1.normalize()
    q2.normalize()
    print("to be cosined: ", (q1.inverted() * q2).w)
    
    try:
    	# return math.acos(clamp((q1.inverted() * q2).w) )
    	return math.acos((q1.inverted() * q2).w) 
    	

    except Exception as e:
    	print("%"*10)
    	print(e.args)
    	return 10

number = 0

def poses_diff(row, pose, unknown):
	global number
	number +=1
	qp = Quaternion()
	qr = Quaternion()
	diff = 0
	l = len(row)
	unknown *= 4

	print("POSE NUMBER : ", number)

	for i,member in enumerate(pose):
		# print("testing index: ", i)
		if i in range(unknown, unknown+4):
			continue

		# print("Stepping on number: ", member)	

		

		qp[i%4] = member 
		qr[i%4] = row[i] 
		
		if i%4==3:
			print("Pose Quat --> ", qp)
			print("Target Quat --> ", qr)

			
			diff += alpha_quats(qp,qr)
			# print("DIFF on i {} --> {}".format(i, partial), "\n")
	
	print(diff, "\n")
	return diff	 


# print("testing diff: ", alpha_quats(Quaternion([.9223, .3078, .1676, .2]), Quaternion([.9223, .3078, .1676, .13])))

print("Poses @ 82 > ", poses[81])


print("Difference btw poses, discarding the middle bone: ", poses_diff(poses[81], targetpose, 1))


nbrs = NearestNeighbors(n_neighbors=3, algorithm='brute', metric= poses_diff, metric_params={"unknown":1}).fit(poses)

number = 0
result = nbrs.kneighbors([targetpose] )

print(result)


# alpha = alpha_quats(w.rotation_quaternion, b.rotation_quaternion)

# print(alpha) 
# t.data.body = str(alpha) 

