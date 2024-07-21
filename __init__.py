bl_info = {
    "name": "Keyframe Tools",
    "blender": (4, 2, 0),
    "category": "Object",
    "version": (1, 0, 1),
    "author": "KSYN",
    "description": "A set of tools for inserting, deleting, and moving keyframes.",
    "location": "View3D > UI > KSYN > Keyframe Inserter/Keyframes",
    "warning": "",
    "doc_url": "",
    "tracker_url": "",
    "support": "COMMUNITY"
}

import bpy

class KeyMapFrameMakerProperties(bpy.types.PropertyGroup):
    key_f_target_object: bpy.props.PointerProperty(
        name="Target Object",
        type=bpy.types.Object,
        description="The object to insert keyframes to"
    ) # type: ignore
    threshold: bpy.props.IntProperty(
        name="Threshold",
        default=10,
        soft_min=1,
        description="Threshold for selecting keyframes near the current frame"
    ) # type: ignore
    include_all: bpy.props.BoolProperty(
        name="Include All",
        default=True,
        description="Include all keyframes or only those near the current frame"
    ) # type: ignore
    

# Add pointer property to the scene properties
def register_properties():
    bpy.utils.register_class(KeyMapFrameMakerProperties)
    bpy.types.Scene.keymapframe_maker = bpy.props.PointerProperty(type=KeyMapFrameMakerProperties)


def unregister_properties():
    del bpy.types.Scene.keymapframe_maker
    bpy.utils.unregister_class(KeyMapFrameMakerProperties)

# Operator to insert keyframes
class OBJECT_OT_insert_keyframe(bpy.types.Operator):
    bl_idname = "object.insert_keyframe"
    bl_label = "Insert Keyframe"
    bl_description = "Insert keyframes to the specified object at the current frame"
    
    def execute(self, context):
        scene = context.scene
        obj = scene.keymapframe_maker.key_f_target_object
        
        
        if obj is None:
            self.report({'WARNING'}, "Target object is not set.")
            return {'CANCELLED'}
        
        current_frame = scene.frame_current
        properties = ['location', 'rotation_euler', 'scale']
        
        for prop in properties:
            obj.keyframe_insert(data_path=prop, frame=current_frame)
        
        self.report({'INFO'}, f"Inserted keyframe to object '{obj.name}' at frame {current_frame}.")
        return {'FINISHED'}

def make_key_maps(obj, include_all=True, threshold=10):
    scene = bpy.context.scene
    threshold = scene.keymapframe_maker.threshold
    
    keyframe_points = sorted({kp.co[0] for fcu in obj.animation_data.action.fcurves for kp in fcu.keyframe_points})
    
    if not include_all:
        current_frame = bpy.context.scene.frame_current
        keyframe_points = [kf for kf in keyframe_points if abs(kf - current_frame) <= threshold]
    
    return keyframe_points

# Operator to move between keyframes
class OBJECT_OT_move_keyframe(bpy.types.Operator):
    bl_idname = "object.move_keyframe"
    bl_label = "Move Keyframe"
    bl_description = "Move between keyframes of the specified object"
    
    direction: bpy.props.EnumProperty(
        name="Direction",
        description="Specify the direction to move the keyframe",
        items=[
            ('PREVIOUS', "Previous", "Move to the previous keyframe"),
            ('NEXT', "Next", "Move to the next keyframe"),
            ('FIRST', "First", "Move to the first keyframe"),
            ('LAST', "Last", "Move to the last keyframe")
        ]
    ) # type: ignore

    def execute(self, context):
        scene = context.scene
        obj = scene.keymapframe_maker.key_f_target_object
        
        if obj is None:
            self.report({'WARNING'}, "Target object is not set.")
            return {'CANCELLED'}
        
        current_frame = scene.frame_current
        keyframe_points = make_key_maps(obj)
        
        if not keyframe_points:
            self.report({'INFO'}, "No keyframes available.")
            return {'CANCELLED'}
        
        if self.direction == 'PREVIOUS':
            previous_keyframes = [kf for kf in keyframe_points if kf < current_frame]
            if previous_keyframes:
                scene.frame_current = int(max(previous_keyframes))
            else:
                scene.frame_current = int(keyframe_points[-1])
            # self.report({'INFO'}, f"Moved to frame {scene.frame_current}.")
        elif self.direction == 'NEXT':
            next_keyframes = [kf for kf in keyframe_points if kf > current_frame]
            if next_keyframes:
                scene.frame_current = int(min(next_keyframes))
            else:
                scene.frame_current = int(keyframe_points[0])
            # self.report({'INFO'}, f"Moved to frame {scene.frame_current}.")
        elif self.direction == 'FIRST':
            scene.frame_current = int(keyframe_points[0])
            # self.report({'INFO'}, f"Moved to the first frame {scene.frame_current}.")
        elif self.direction == 'LAST':
            scene.frame_current = int(keyframe_points[-1])
            # self.report({'INFO'}, f"Moved to the last frame {scene.frame_current}.")
        
        return {'FINISHED'}

# Operator to delete the current keyframe
class OBJECT_OT_delete_keyframe(bpy.types.Operator):
    bl_idname = "object.delete_keyframe"
    bl_label = "Delete Keyframe"
    bl_description = "Delete the keyframe of the specified object at the current frame"
    
    def execute(self, context):
        scene = context.scene
        obj = scene.keymapframe_maker.key_f_target_object
        
        if obj is None:
            self.report({'WARNING'}, "Target object is not set.")
            return {'CANCELLED'}
        
        current_frame = scene.frame_current
        properties = ['location', 'rotation_euler', 'scale']
        
        for prop in properties:
            obj.keyframe_delete(data_path=prop, frame=current_frame)
        
        self.report({'INFO'}, f"Deleted keyframe of object '{obj.name}' at frame {current_frame}.")
        return {'FINISHED'}
    
def calculate_differences(current_frame, previous_keyframe, next_keyframe):
    if current_frame is not None and previous_keyframe is not None:
        prev_difference = current_frame - previous_keyframe
    else:
        prev_difference = None  # Set appropriate default value if needed

    if current_frame is not None and next_keyframe is not None:
        next_difference = next_keyframe - current_frame
    else:
        next_difference = None  # Set appropriate default value if needed

    return prev_difference, next_difference

def prev_label(layout, prev):
    layout.label(text=f"    {prev}", icon='SORT_DESC')
    
def next_label(layout, next_):
    layout.label(text=f"    {next_}", icon='SORT_ASC')


def layout_label(layout, keyframe_points, current_frame, next_keyframe, previous_keyframe):
    for frame in keyframe_points:
        prev, next_ = calculate_differences(current_frame, previous_keyframe, next_keyframe)
                
        if frame == current_frame:
            prev_label(layout, prev)
            layout.label(text=f" {frame}", icon='DECORATE_KEYFRAME')
            next_label(layout, next_)
        else:
            layout.label(text=f"{frame}", icon="KEYFRAME")
            
        if current_frame not in keyframe_points:
            if frame == previous_keyframe:
                prev_label(layout, prev)
                layout.label(text=f"    {current_frame}", icon='RIGHTARROW')
                next_label(layout, next_)
        
def create_keymap_list(keyframe_points, scene):
    current_frame = scene.frame_current
    previous_keyframe = None
    next_keyframe = None
    
    for frame in keyframe_points:
        if frame < current_frame:
            previous_keyframe = frame
        elif frame > current_frame and next_keyframe is None:
            next_keyframe = frame
    
    # If next_keyframe is not found, compare with the last frame of the playback rendering range
    if next_keyframe is None:
        next_keyframe = scene.frame_end
    
    # If previous_keyframe is not found, compare with the first frame of the playback rendering range
    if previous_keyframe is None:
        previous_keyframe = scene.frame_start
    
    return previous_keyframe, next_keyframe, current_frame

def draw_keyframes(layout, obj, scene):
    if obj is not None and obj.animation_data and obj.animation_data.action:
        layout.label(text="Keyframes:")
#        keyframe_points = sorted({int(kp.co[0]) for fcu in obj.animation_data.action.fcurves for kp in fcu.keyframe_points})
        include_all = scene.keymapframe_maker.include_all
        
        keyframe_points = make_key_maps(obj,include_all=include_all)
        if not keyframe_points:
            return
        
        previous_keyframe, next_keyframe, current_frame = create_keymap_list(keyframe_points, scene)
        
        layout_label(layout, keyframe_points, current_frame, next_keyframe, previous_keyframe)


# Define the panel
class OBJECT_PT_keyframe_panel(bpy.types.Panel):
    bl_label = "Keyframe Inserter"
    bl_idname = "OBJECT_PT_keyframe_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'KSYN'
    
    def draw_header(self, context):
        layout = self.layout
        layout.label(icon='DECORATE_KEYFRAME')  # Specify the icon

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        obj = scene.keymapframe_maker.key_f_target_object
        
        layout.prop(scene.keymapframe_maker, "key_f_target_object")
        row = layout.row(align=True)
        row.operator("object.insert_keyframe", icon='KEY_HLT', text="Insert Key")
        row.operator("object.delete_keyframe", icon='KEY_DEHLT', text="Delete Key")
        
        row = layout.row(align=True)
        row.operator("object.move_keyframe", text="", icon='PREV_KEYFRAME').direction = 'FIRST'
        row.separator(factor=2.0)  # Add spacing
        row.operator("object.move_keyframe", text="", icon='TRIA_LEFT').direction = 'PREVIOUS'
        row.separator(factor=2.0)  # Add spacing
        row.prop(scene, "frame_current", text="")
        row.separator(factor=2.0)  # Add spacing
        row.operator("object.move_keyframe", text="", icon='TRIA_RIGHT').direction = 'NEXT'
        row.separator(factor=2.0)  # Add spacing
        row.operator("object.move_keyframe", text="", icon='NEXT_KEYFRAME').direction = 'LAST'

# Define the Keyframes panel
class OBJECT_PT_keyframes_panel(bpy.types.Panel):
    bl_label = "Keyframes"
    bl_idname = "OBJECT_PT_keyframes_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'KSYN'
    
    def draw_header(self, context):
        layout = self.layout
        layout.label(icon='DECORATE_KEYFRAME')  # Specify the icon

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        layout.prop(scene.keymapframe_maker, "include_all")
        if not scene.keymapframe_maker.include_all:
            layout.prop(scene.keymapframe_maker, "threshold")
        
#        target_object = scene.keymapframe_maker.keymapframe_maker.key_f_target_object

        obj = scene.keymapframe_maker.key_f_target_object
        
        draw_keyframes(layout, obj, scene)

# Function to register properties and operators
def register():
    register_properties()
    bpy.utils.register_class(OBJECT_OT_insert_keyframe)
    bpy.utils.register_class(OBJECT_OT_move_keyframe)
    bpy.utils.register_class(OBJECT_OT_delete_keyframe)
    bpy.utils.register_class(OBJECT_PT_keyframe_panel)
    bpy.utils.register_class(OBJECT_PT_keyframes_panel)

# Function to unregister properties and operators
def unregister():
    unregister_properties()
    bpy.utils.unregister_class(OBJECT_OT_insert_keyframe)
    bpy.utils.unregister_class(OBJECT_OT_move_keyframe)
    bpy.utils.unregister_class(OBJECT_OT_delete_keyframe)
    bpy.utils.unregister_class(OBJECT_PT_keyframe_panel)
    bpy.utils.unregister_class(OBJECT_PT_keyframes_panel)

# Execute the registration
if __name__ == "__main__":
    register()
