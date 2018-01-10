import numpy as np 
import npytypes.quaternion


a = np.quaternion(0.9223, 0.3078, 0.1676, 0.1360)

b = a.conjugate()

def print_q(quat):
	print("quat[ {}, {}, {}, {} ]".format(quat.w,quat.x,quat.y,quat.z))


c = np.multiply(a, b)

print_q(c)


import mpmath as mp 

class mpquat:
	mp.mp.dps = 50

	def __init__(self, w=1, x=0, y=0, z=0):
		self.w = mp.mpf(w)
		self.x = mp.mpf(x)
		self.y = mp.mpf(y)
		self.z = mp.mpf(z)


	def conjugate(self):
		self.x = -self.x
		self.y = -self.y
		self.z = -self.z

	def multiply(q, r):
		"""Return the product of this and other quaternion
		from https://www.mathworks.com/help/aeroblks/quaternionmultiplication.html"""
		t = mpquat()
		t.w = r.w*q.w - r.x*q.x - r.y*q.y - r.z*q.z
		t.x = r.w*q.x + r.x*q.w - r.y*q.z + r.z*q.y
		t.y = r.w*q.y + r.x*q.z + r.y*q.w - r.z*q.x
		t.z = r.w*q.z - r.x*q.y + r.y*q.x + r.z*q.w
		return t
		
print("#"*50,"\n")

aa = mpquat(0.9223, 0.3078, 0.1676, 0.1360)
aa.conjugate()

bb = mpquat(0.9223, 0.3078, 0.1676, 0.1360)
aa.multiply(bb)

print_q(aa)