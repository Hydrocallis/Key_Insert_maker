bl_info = {
    "name": "Keyframe Tools",
    "blender": (4, 2, 0),
    "category": "Object",
    "version": (1, 0, 4),
    "author": "KSYN",
    "description": "A set of tools for inserting, deleting, and moving keyframes.",
    "location": "View3D > UI > KSYN > Keyframe Inserter/Keyframes",
    "warning": "",
    "doc_url": "",
    "tracker_url": "",
    "support": "COMMUNITY"
}

import bpy
from bpy.types import AddonPreferences, Panel,Operator
from bpy.props import StringProperty

# プロパティクラスの定義
class ShowPanel():
    show_draw_constraint: bpy.props.BoolProperty(
        name="Show Draw Constraint",
        description="Toggle Draw Constraint",
        default=True
    ) # type: ignore

class KeyMapFrameMakerProperties_op():
    speed: bpy.props.FloatProperty(
        name="Speed",
        description="Animation speed",
        default=1.0,
        min=0,
        max=1000.0
    ) # type: ignore
    direction: bpy.props.EnumProperty(
        name="Direction",
        description="Playback direction",
        items=[
            ('FORWARD', "Forward", "Play animation forward"),
            ('BACKWARD', "Backward", "Play animation backward")
        ],
        default='FORWARD'
    ) # type: ignore
    operator_status: bpy.props.StringProperty(
        name="Operator Status",
        description="Status of the modal operator",
        default="Not Running"
    ) # type: ignore

class KeyMapFrameMakerProperties(bpy.types.PropertyGroup,KeyMapFrameMakerProperties_op,ShowPanel):
    constraints: bpy.props.EnumProperty(
        name="Constraints",
        description="List of constraints for the selected object",
        items=lambda self, context: [
            (c.name, c.name, c.type) for c in context.scene.keymapframe_maker.key_f_target_object.constraints
        ] if context.scene.keymapframe_maker.key_f_target_object and context.scene.keymapframe_maker.key_f_target_object.constraints else [("None", "None", "No constraints available")]
    ) # type: ignore
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

def make_constant_dict(obj,key_maps_dict):
    target_constraint = bpy.context.scene.keymapframe_maker.constraints

    # Check for 'AutoTrack' constraint keyframes
    # target_constraint = "AutoTrack"

    if obj is not None and target_constraint in obj.constraints:
        constraint_name = obj.constraints[target_constraint].name

        for action in bpy.data.actions:
            for fcurve in action.fcurves:
                if fcurve.data_path == f'constraints["{constraint_name}"].influence':
                    constraint_keyframes = [keyframe.co[0] for keyframe in fcurve.keyframe_points]
                    key_maps_dict["Constraint Keyframes"] = constraint_keyframes
                    # break  # Found the constraint, no need to continue searching
                else:
                    key_maps_dict["Constraint Keyframes"] = []

    else:
        # If no 'AutoTrack' constraint is found
        key_maps_dict["Constraint Keyframes"] = []
    return key_maps_dict["Constraint Keyframes"]

def make_key_maps(obj, include_all=True, threshold=10):
    scene = bpy.context.scene
    threshold = scene.keymapframe_maker.threshold
    
    # Collect all keyframe points
    keyframe_points = sorted({kp.co[0] for fcu in obj.animation_data.action.fcurves for kp in fcu.keyframe_points})
    
    if not include_all:
        current_frame = bpy.context.scene.frame_current
        keyframe_points = [kf for kf in keyframe_points if abs(kf - current_frame) <= threshold]
    
    # Dictionary to store keyframe points
    key_maps_dict = {"All Keyframes": keyframe_points}

    # Collect keyframes for different animation data paths
    animation_data_paths = ["location", "rotation_euler", "scale"]
    for path in animation_data_paths:
        path_keyframes = sorted({kp.co[0] for fcu in obj.animation_data.action.fcurves if path in fcu.data_path for kp in fcu.keyframe_points})
        key_maps_dict[f"{path.capitalize()} Keyframes"] = path_keyframes

    key_maps_dict["Constraint Keyframes"] = make_constant_dict(obj,key_maps_dict)

    # Find matching frames
    all_keyframes = key_maps_dict["All Keyframes"]
    constraint_keyframes = key_maps_dict["Constraint Keyframes"]
    matching_keyframes = sorted(set(all_keyframes) & set(constraint_keyframes))
    key_maps_dict["Matching Keyframes"] = matching_keyframes
    return key_maps_dict
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
        current_frame = scene.frame_current

        
        if obj is None:
            self.report({'WARNING'}, "Target object is not set.")
            return {'CANCELLED'}
        
        elif not obj.animation_data or not obj.animation_data.action:
            self.report({'WARNING'}, "Target object has no keyframes.")
            return {'CANCELLED'}
        
        key_maps_dict = make_key_maps(obj)
        all_keyframes = key_maps_dict.get("All Keyframes", [])
        
        if not all_keyframes:
            self.report({'INFO'}, "No keyframes available.")
            return {'CANCELLED'}
        
        if self.direction == 'PREVIOUS':
            previous_keyframes = [kf for kf in all_keyframes if kf < current_frame]
            if previous_keyframes:
                scene.frame_current = int(max(previous_keyframes))
            else:
                scene.frame_current = int(all_keyframes[-1])
            # self.report({'INFO'}, f"Moved to frame {scene.frame_current}.")
        elif self.direction == 'NEXT':
            next_keyframes = [kf for kf in all_keyframes if kf > current_frame]
            if next_keyframes:
                scene.frame_current = int(min(next_keyframes))
            else:
                scene.frame_current = int(all_keyframes[0])
            # self.report({'INFO'}, f"Moved to frame {scene.frame_current}.")
        elif self.direction == 'FIRST':
            scene.frame_current = int(all_keyframes[0])
            # self.report({'INFO'}, f"Moved to the first frame {scene.frame_current}.")
        elif self.direction == 'LAST':
            scene.frame_current = int(all_keyframes[-1])
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

def layout_label(layout, all_keyframes, current_frame, next_keyframe, previous_keyframe, key_maps_dict):
    matching_keyframes = key_maps_dict["Matching Keyframes"]
    location_keyframes = key_maps_dict["Location Keyframes"]
    rotation_keyframes = key_maps_dict["Rotation_euler Keyframes"]
    scale_keyframes = key_maps_dict["Scale Keyframes"]
    
    for frame in all_keyframes:
        prev, next_ = calculate_differences(current_frame, previous_keyframe, next_keyframe)
                
        if frame == current_frame:
            prev_label(layout, prev)
            row = layout.row(align=True)
            row.label(text=f" {frame}", icon='DECORATE_KEYFRAME')
            if frame in matching_keyframes:
                row.label(text="", icon="CON_TRACKTO")
            if frame in location_keyframes:
                row.label(text="", icon="OUTLINER_OB_EMPTY")
            if frame in rotation_keyframes:
                row.label(text="", icon="ORIENTATION_LOCAL")
            if frame in scale_keyframes:
                row.label(text="", icon="FULLSCREEN_ENTER")
            next_label(layout, next_)
        else:
            row = layout.row(align=True)
            row.label(text=f" {frame}", icon='KEYFRAME')
            if frame in matching_keyframes:
                row.label(text="", icon="CON_TRACKTO")
            if frame in location_keyframes:
                row.label(text="", icon="OUTLINER_OB_EMPTY")
            if frame in rotation_keyframes:
                row.label(text="", icon="ORIENTATION_LOCAL")
            if frame in scale_keyframes:
                row.label(text="", icon="FULLSCREEN_ENTER")

        if current_frame not in all_keyframes:
            if frame == previous_keyframe:
                prev_label(layout, prev)
                row = layout.row(align=True)
                row.label(text=f"    {current_frame}", icon='RIGHTARROW')
                # if frame in matching_keyframes:
                #     row.label(text="", icon="CON_TRACKTO")
                # if frame in location_keyframes:
                #     row.label(text="", icon="OUTLINER_OB_EMPTY")
                # if frame in rotation_keyframes:
                #     row.label(text="", icon="ORIENTATION_LOCAL")
                # if frame in scale_keyframes:
                #     row.label(text="", icon="FULLSCREEN_ENTER")
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
        keyframe_points = sorted({int(kp.co[0]) for fcu in obj.animation_data.action.fcurves for kp in fcu.keyframe_points})
        include_all = scene.keymapframe_maker.include_all
        

        # Get keyframe data
        key_maps_dict = make_key_maps(obj, include_all=include_all)
        all_keyframes = key_maps_dict.get("All Keyframes", [])
        matching_keyframes = key_maps_dict.get("Matching Keyframes", [])
        
        if not all_keyframes:
            return
        
        previous_keyframe, next_keyframe, current_frame = create_keymap_list(all_keyframes, scene)
        
        layout_label(layout, all_keyframes, current_frame, next_keyframe, previous_keyframe, key_maps_dict)
# Define the panel
class OBJECT_PT_keyframe_panel(bpy.types.Panel):
    bl_label = "Keyframe Inserter"
    bl_idname = "OBJECT_PT_keyframe_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'KSYN'



    def draw_constrains_elect(self, context):
        layout = self.layout
        props = context.scene.keymapframe_maker
        obj = context.scene.keymapframe_maker.key_f_target_object

        if obj:
            layout.prop(props, "constraints", text="Constraint")

            # 選択されたコンストレイントの名前を表示
            if props.constraints != "None":
                constraint = obj.constraints.get(props.constraints)
                if constraint:
                    layout.label(text=f"Constraint Name: {constraint.name}")
                    layout.label(text=f"Constraint Type: {constraint.type}")
            else:
                layout.label(text="No constraints available.")
        else:
            layout.label(text="No object selected.")
    
    def draw_framerate(self, layout, rd):
        col = layout.column(align=True)
        col.prop(rd, "fps")
        col.prop(rd, "fps_base", text="Base")
            
    def draw_header(self, context):
        layout = self.layout
        layout.label(icon='DECORATE_KEYFRAME')  # Specify the icon
        layout.operator(KYSYNKFM_OpenAddonPreferencesOperator.bl_idname,text="",icon="TOOL_SETTINGS")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        # rd = context.scene.render
        
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
        row = layout.row(align=True)
        
        # self.draw_framerate(row, rd)
        view = context.space_data
        row = layout.row(align=True)
        
        row.prop(view, "lock_camera", text="Camera to View")
        props = scene.keymapframe_maker

        row = layout.row()
        icon = 'DOWNARROW_HLT' if props.show_draw_constraint else 'RIGHTARROW'
        row.prop(props, "show_draw_constraint", text="", icon=icon, emboss=False)
        row.label(text="Show Constraint")
        if props.show_draw_constraint:
            self.draw_constrains_elect(context)
            self.draw_constraint(context)

    def draw_constraint(self, context):
        layout = self.layout
        select_constraints_name = context.scene.keymapframe_maker.constraints
        obj = context.scene.keymapframe_maker.key_f_target_object
        
        if obj is not None and select_constraints_name in obj.constraints:
            constraint = obj.constraints[select_constraints_name]
            layout.label(text=f"This is the display of {select_constraints_name} Constraint")
            layout.prop(constraint, "enabled")
            layout.prop(constraint, "influence")
        else:
            layout.label(text="No 'AutoTrack' constraint found.")
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

class OBJECT_OT_animated_playback(bpy.types.Operator):
    bl_idname = "object.animated_playback"
    bl_label = "Animated Playback Operator"
    bl_options = {'REGISTER', 'UNDO'}

    _timer = None
    _count = 0
    _count_max = 0

    def modal(self, context, event):
        props = context.scene.keymapframe_maker
        
        if event.type in {'SPACE', 'ESC', 'LEFTMOUSE', 'RIGHTMOUSE'}:
            self.cancel(context)
            return {'CANCELLED'}
        
        if event.type == 'TIMER':
            self._count += 1
            
            if self._count >= self._count_max:
                scene = context.scene
                new_frame = scene.frame_current
                
                if props.direction == 'FORWARD':
                    new_frame += 1
                    if new_frame > scene.frame_end:
                        new_frame = scene.frame_start + (new_frame - scene.frame_end - 1)
                else:
                    new_frame -= 1
                    if new_frame < scene.frame_start:
                        new_frame = scene.frame_end - (scene.frame_start - new_frame - 1)
                
                scene.frame_current = int(new_frame)
                self.update_panel(context)
                self._count = 0
        
        if event.type == 'UP_ARROW' or event.type == 'WHEELUPMOUSE':
            props.speed = min(10.0, props.speed + 0.1)
            self.report({'INFO'}, f"Speed increased to {props.speed:.1f}")
            self.reset_timer(context)
        
        if event.type == 'DOWN_ARROW' or event.type == 'WHEELDOWNMOUSE':
            props.speed = max(0.01, props.speed - 0.1)
            self.report({'INFO'}, f"Speed decreased to {props.speed:.1f}")
            self.reset_timer(context)
        
        if event.type == 'RIGHT_ARROW':
            props.direction = 'FORWARD'
            self.report({'INFO'}, "Playback direction set to FORWARD")
        
        if event.type == 'LEFT_ARROW':
            props.direction = 'BACKWARD'
            self.report({'INFO'}, "Playback direction set to BACKWARD")
        
        if event.type == 'MIDDLEMOUSE' and event.value == 'PRESS':
            if props.direction == 'FORWARD':
                props.direction = 'BACKWARD'
                self.report({'INFO'}, "Playback direction set to BACKWARD")
            else:
                props.direction = 'FORWARD'
                self.report({'INFO'}, "Playback direction set to FORWARD")
        # ヘッダーにモーダルオペレーターの状況を表示
        context.area.header_text_set(f"Frame: {context.scene.frame_current}, Speed: {props.speed:.1f}, Direction: {props.direction}")


        return {'RUNNING_MODAL'}

    
    def execute(self, context):
        self.reset_timer(context)
        context.window_manager.modal_handler_add(self)
        context.scene.keymapframe_maker.operator_status = "Running"
        # ステータスに入力キーのヒントを設定
        context.workspace.status_text_set("ESC/SPACE/LEFTMOUSE/RIGHTMOUSE: Stop, UP_ARROW/WHEELUP: Increase Speed, DOWN_ARROW/WHEELDOWN: Decrease Speed, LEFT_ARROW: Backward, RIGHT_ARROW: Forward, MIDDLEMOUSE: Toggle Direction")
        
        return {'RUNNING_MODAL'}
    
    def reset_timer(self, context):
        props = context.scene.keymapframe_maker
        if self._timer is not None:
            context.window_manager.event_timer_remove(self._timer)
        
        fps = context.scene.render.fps
        interval = 1.0 / (fps * props.speed)
        if interval < 0.001:
            interval = 0.001
        self._count_max = int(fps / props.speed)
        self._timer = context.window_manager.event_timer_add(interval, window=context.window)

    def update_panel(self, context):
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()

    def cancel(self, context):
        if self._timer is not None:
            context.window_manager.event_timer_remove(self._timer)
        self._timer = None


        context.scene.keymapframe_maker.operator_status = "Stopped"
        
        # ヘッダーとステータスをクリア
        context.area.header_text_set(None)
        context.workspace.status_text_set(None)
        
        context.area.tag_redraw()
        return {'CANCELLED'}

# パネルの定義
class MY_PT_AnimatedPlaybackPanel(bpy.types.Panel):
    bl_label = "Keyframes Animation Control"
    bl_idname = "OBJECT_PT_keyframes_animated_playback_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'KSYN'

    def draw_header(self, context):
        layout = self.layout
        layout.label(icon='DECORATE_KEYFRAME')  # Specify the icon


    def draw(self, context):
        layout = self.layout
        props = context.scene.keymapframe_maker
        layout.label(text="Current Frame: {}".format(int(context.scene.frame_current)))
        
        row = layout.row()
        if props.operator_status == "Running" and props.direction == "FORWARD":
            row.label(text="Operator Status:", icon='PLAY')
        elif props.operator_status == "Running" and props.direction == "BACKWARD":
            row.label(text="Operator Status:", icon='PLAY_REVERSE')
        else:
            row.label(text="Operator Status:", icon='PAUSE')
        row.label(text=props.operator_status)

        layout.prop(props, "speed", text="Speed")
        layout.prop(props, "direction", text="Direction")
        layout.operator("object.animated_playback", text="Start Animated Playback")

# アドオンプレファレンスの定義
class KYSYNKFM_MyAddonPreferences(AddonPreferences):
    bl_idname = __name__

    category_keyframe: StringProperty(
        name="Keyframe Panel Category",
        description="Choose a name for the category of the Keyframe panel",
        default="KSYN",
        update=lambda self, context: update_panel_category(self, context)
    ) # type: ignore
    category_keyframes: StringProperty(
        name="Keyframes Panel Category",
        description="Choose a name for the category of the Keyframes panel",
        default="KSYN",
        update=lambda self, context: update_panel_category(self, context)
    ) # type: ignore
    category_playback: StringProperty(
        name="Animated Playback Panel Category",
        description="Choose a name for the category of the Animated Playback panel",
        default="KSYN",
        update=lambda self, context: update_panel_category(self, context)
    ) # type: ignore

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "category_keyframe")
        layout.prop(self, "category_keyframes")
        layout.prop(self, "category_playback")

# プレファレンス画面を開くオペレーターの定義
class KYSYNKFM_OpenAddonPreferencesOperator(Operator):
    bl_idname = "ksynkfmpreferences.open_my_addon_prefs"
    bl_label = "Open Addon Preferences"

    def execute(self, context):
        bpy.ops.screen.userpref_show('INVOKE_DEFAULT')
        bpy.context.preferences.active_section = 'ADDONS'
        addon = bpy.context.preferences.addons[__name__]
        bpy.ops.preferences.addon_expand(module=addon.module)
        bpy.ops.preferences.addon_show(module = addon.module)

        return {'FINISHED'}

def update_panel_category(self, context):
    register_panels()
def update_panel_category(self, context):
    register_panels()
    
def register_panels():
    panels = [
        (MY_PT_AnimatedPlaybackPanel, "category_playback"),
        (OBJECT_PT_keyframe_panel, "category_keyframe"),
        (OBJECT_PT_keyframes_panel, "category_keyframes"),
    ]

    addon_prefs = bpy.context.preferences.addons[__name__].preferences

    for panel, category_attr in panels:
        try:
            bpy.utils.unregister_class(panel)
        except:
            pass

        panel.bl_category = getattr(addon_prefs, category_attr)
        bpy.utils.register_class(panel)

classes = [
    OBJECT_OT_animated_playback,
    OBJECT_OT_insert_keyframe,
    OBJECT_OT_move_keyframe,
    OBJECT_OT_delete_keyframe,
    KYSYNKFM_MyAddonPreferences,
    KYSYNKFM_OpenAddonPreferencesOperator,
]
# Function to register properties and operators
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    register_properties()
    register_panels()

# Function to unregister properties and operators
def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    unregister_properties()
    panels = [
        OBJECT_PT_keyframe_panel,
        OBJECT_PT_keyframes_panel,
        MY_PT_AnimatedPlaybackPanel
    ]
    for panel in panels:
        bpy.utils.unregister_class(panel)


# Execute the registration
if __name__ == "__main__":
    register()
