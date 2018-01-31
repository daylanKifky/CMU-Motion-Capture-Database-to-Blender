
"""EXAMPLE OF MODAL OPERATOR """

import bpy

from bpy.props import IntProperty, FloatProperty
from mathutils import *
from math import *

from os import system
from os import path
from sys import path as syspath


syspath.append(path.dirname(bpy.data.filepath))

import Chordata_Armature as chordata
from importlib import reload
reload(chordata)

system("clear")

D = bpy.data
D = bpy.data
C = bpy.context


class ReceiveOperator(bpy.types.Operator):
   
    """Receive quaternions from OSC and move an armature"""
    bl_idname = "object.receive_operator"
    bl_label = "Receive Chordata Armature"
   
    views_3d =  [area for area in bpy.context.screen.areas if area.type == 'VIEW_3D' ]  

    def __init__(self):
        self.chord = chordata.Chordata()
        self.last_event = ""

    def invoke(self, context, event):
        """Start the timer"""

        # return {'FINISHED'}
        
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.05, context.window)
        wm.modal_handler_add(self)

        self.chord.start_server()
        
        self.text(self.chord.message)


        D.scenes['Scene'].layers[0] = True
        D.scenes['Scene'].layers[1] = True
        D.scenes['Scene'].layers[2] = True

        return {'RUNNING_MODAL'}

    def text(self, text):
        for a in self.views_3d:
                a.header_text_set(text)
        

    def modal(self, context, event):

        if event.type == 'TIMER':
            self.chord.put_quad_on_bones()

        elif event.type == 'A':
            self.chord.get_rot_diff()
            self.text(self.chord.message)

        elif event.type == "Q":
            D.scenes['Scene'].layers[0] = False



        elif event.type == "W":
            D.scenes['Scene'].layers[1] = False

        elif event.type == "E":
            D.scenes['Scene'].layers[2] = False

        elif event.type == "R":
            D.scenes['Scene'].layers[0] = True
            D.scenes['Scene'].layers[1] = True
            D.scenes['Scene'].layers[2] = True


        # elif event.type == 'LEFTMOUSE':
        #     self.cancel(context)
        #     return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            self.cancel(context)
            return {'CANCELLED'}

        self.last_event = event.type

        return {'RUNNING_MODAL'}

        

    def cancel(self, context):
        """
        cancel() get's called when the operator is about to exit
        Here we remove the timer and stop the server
        """
        wm = context.window_manager
        wm.event_timer_remove(self._timer)

        self.text("Closing server..")
        # self.chord.close_server()
        
        self.chord.server.shutdown()
        self.chord.st.join()
        
        for a in self.views_3d:
            a.header_text_set()

    # ###########################################
    # ###     DEFINING CUSTOM METHODS         ###
    # ###########################################

        
        

def register():
    bpy.utils.register_class(ReceiveOperator)


def unregister():
    bpy.utils.unregister_class(ReceiveOperator)


if __name__ == "__main__":
    register()

    # test call
    bpy.ops.object.receive_operator('INVOKE_DEFAULT')
