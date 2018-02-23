# #########################
# Create empties, axis and (no well orieted) rotation arcs
# #########################
ZPu.mode_set(self.target, context, "OBJECT")
for name, rot in self.slerps.items():
    bpy.ops.object.empty_add(
        location = self.target.matrix_world* self.target.pose.bones[name].matrix.to_translation(), 
        rotation=rot.to_euler(),
        type='ARROWS', radius=0.2)

for name, m in self.slerps.items():
    bpy.ops.object.empty_add(
        location = m.to_translation(), 
        rotation=m.to_euler(),
        type='ARROWS', radius=0.2)


for name, empty in self.twists.items():
    bpy.ops.object.empty_add(location = self.target.matrix_world* empty[0], rotation=empty[1].to_euler(),
        type='ARROWS', radius=0.2)

    # curve_rot = Quaternion((1,0,0,0)) * empty[1].conjugated()
    bpy.ops.curve.simple(Simple_Type ="Arc", Simple_startlocation= self.target.matrix_world* empty[0], 
        Simple_angle=empty[1].angle, Simple_degrees_or_radians = "Radians", 
        Simple_rotation_euler = empty[1].to_euler(), Simple_radius=0.1)

    ZPu.create_direction_obj(name, self.target.matrix_world* empty[0], empty[1].axis *0.2)
