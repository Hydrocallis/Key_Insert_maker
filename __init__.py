bl_info = {
    "name": "Keyframe Tools",
    "blender": (4, 2, 0),
    "category": "Object",
    "version": (1, 0, 6),
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
import bpy
from bpy.app.handlers import persistent

# constraintのリスト内
class KYSYNKFM_PG_ConstraintItem(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Name") # type: ignore
    type: bpy.props.StringProperty(name="Type") # type: ignore
# constraintリストのコレクション
class KYSYNKFM_PG_ConstraintsProperties(bpy.types.PropertyGroup):
    constraints: bpy.props.CollectionProperty(type=KYSYNKFM_PG_ConstraintItem) # type: ignore
    constraints_index: bpy.props.IntProperty(name="Index", default=0) # type: ignore
    constraints_select: bpy.props.CollectionProperty(type=KYSYNKFM_PG_ConstraintItem) # type: ignore
    constraints_select_index: bpy.props.IntProperty(name="Index", default=0) # type: ignore
# エフカーブのリスト内
class KYSYNKFM_PG_FCurvePropertyGroup(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="F-Curve Path") # type: ignore
# エフカーブのリスト内
class KYSYNKFM_PG_Fcurves(bpy.types.PropertyGroup):
    active_fcurves: bpy.props.CollectionProperty(type=KYSYNKFM_PG_FCurvePropertyGroup) # type: ignore
    select_fcurves: bpy.props.CollectionProperty(type=KYSYNKFM_PG_FCurvePropertyGroup) # type: ignore
    
    active_index: bpy.props.IntProperty() # type: ignore
    select_index: bpy.props.IntProperty() # type: ignore
    
    object: bpy.props.PointerProperty(
        name="Target Object",
        type=bpy.types.Object,
        description="Target object to get F-Curve paths from"
    ) # type: ignore

    def update_active_fcurves(self, context):
        self.active_fcurves.clear()
        obj = context.active_object
        if obj and obj.animation_data:
            for fcurve in obj.animation_data.action.fcurves:
                item = self.active_fcurves.add()
                item.name = fcurve.data_path

 
                
    def update_select_fcurves(self, context):
        self.select_fcurves.clear()
        obj =context.scene.keymapframe_maker.key_f_target_object
        if obj and obj.animation_data:
            for fcurve in obj.animation_data.action.fcurves:
                item = self.select_fcurves.add()
                item.name = fcurve.data_path
# パネルON　OFF関係のプロパティクラスの定義
class KYSYNKFM_PG_ShowPanel():
    show_draw_constraint: bpy.props.BoolProperty(
        name="Show Draw Constraint",
        description="Toggle Draw Constraint",
        default=True
    ) # type: ignore

class KYSYNKFM_PG_KeyMapAnimeFrameMakerProperties():
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

class KYSYNKFM_PG_KeyMapFrameMake(bpy.types.PropertyGroup,KYSYNKFM_PG_KeyMapAnimeFrameMakerProperties,KYSYNKFM_PG_ShowPanel):
    anime_fcurves_props : bpy.props.PointerProperty(type=KYSYNKFM_PG_Fcurves) # type: ignore

    constraints_props  : bpy.props.PointerProperty(type=KYSYNKFM_PG_ConstraintsProperties) # type: ignore

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
#プロパティとアップデートハンドラー関係
class RegisterProperties:

    register_properties_class=[
        KYSYNKFM_PG_ConstraintItem,
        KYSYNKFM_PG_ConstraintsProperties,
        KYSYNKFM_PG_FCurvePropertyGroup,
        KYSYNKFM_PG_Fcurves,
        KYSYNKFM_PG_KeyMapFrameMake,
                            ]           
    # コレクションを更新するハンドラー(デコレーターをつけて永続的に) https://docs.blender.org/api/current/bpy.app.handlers.html
    @staticmethod
    @persistent
    def update_constraints_fcurves(scene):
        #コンスタントリストのアップデート
        crprops = scene.keymapframe_maker.constraints_props
        target_object = scene.keymapframe_maker.key_f_target_object  # ここでアクティブオブジェクトを読み込む
        
        if target_object:
            constraints = crprops.constraints
            constraints.clear()
            for c in target_object.constraints:
                item = constraints.add()
                item.name = c.name
                item.type = c.type


        if bpy.context.object:
            constraints_select = crprops.constraints_select
            constraints_select.clear()
            for c in bpy.context.object.constraints:
                item = constraints_select.add()
                item.name = c.name
                item.type = c.type

        # エフカーブのアップデート
        scene.keymapframe_maker.anime_fcurves_props.update_active_fcurves(bpy.context)
        scene.keymapframe_maker.anime_fcurves_props.update_select_fcurves(bpy.context)


    def register_properties(self):
        for cls in self.register_properties_class:
            bpy.utils.register_class(cls)
        bpy.types.Scene.keymapframe_maker = bpy.props.PointerProperty(type=KYSYNKFM_PG_KeyMapFrameMake)
        bpy.app.handlers.depsgraph_update_post.append(RegisterProperties.update_constraints_fcurves)

    def unregister_properties(self):
        for cls in self.register_properties_class:
            bpy.utils.unregister_class(cls)
        del bpy.types.Scene.keymapframe_maker
        bpy.app.handlers.depsgraph_update_post.remove(RegisterProperties.update_constraints_fcurves)
# Operator to insert keyframes
class KYSYNKFM_OT_insert_keyframe(bpy.types.Operator):
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

class MakeKeyMaps:
    def make_constant_dict(self, obj, key_maps_dict):
        ##インデックスのチェック
        scene = bpy.context.scene
        crprops=scene.keymapframe_maker.constraints_props

        if obj==bpy.context.object:
            # オブジェクトのコンストレインの値を確認するなけれれば無いとリターンする。
            if crprops.constraints_select_index >= 0 and crprops.constraints_select_index < len(crprops.constraints_select):
                target_constraint = crprops.constraints_select[crprops.constraints_select_index].name
            else:
                key_maps_dict["Constraint Keyframes"] = []
                return key_maps_dict["Constraint Keyframes"]
        else:
            
            if crprops.constraints_index >= 0 and crprops.constraints_index < len(crprops.constraints):

                target_constraint = crprops.constraints[crprops.constraints_index].name
            else:
                key_maps_dict["Constraint Keyframes"] = []
                return key_maps_dict["Constraint Keyframes"]

        if bpy.context.scene.keymapframe_maker.key_f_target_object==bpy.context.object:
            if crprops.constraints_index >= 0 and crprops.constraints_index < len(crprops.constraints):

                target_constraint = crprops.constraints[crprops.constraints_index].name
            else:
                key_maps_dict["Constraint Keyframes"] = []
                return key_maps_dict["Constraint Keyframes"]
    



        # target_constraint = "AutoTrack"  # 'AutoTrack' というコンストレイン名を対象にする
        if obj is not None and target_constraint in obj.constraints:
            constraint_name = obj.constraints[target_constraint].name

            # 指定されたオブジェクトのアクションを取得
            if obj.animation_data and obj.animation_data.action:
                action = obj.animation_data.action
                constraint_keyframes = []
                for fcurve in action.fcurves:
                    if fcurve.data_path.startswith(f'constraints["{constraint_name}"].'):
                        if 'influence' in fcurve.data_path or 'offset' in fcurve.data_path:
                            constraint_keyframes.extend([keyframe.co[0] for keyframe in fcurve.keyframe_points])
                key_maps_dict["Constraint Keyframes"] = constraint_keyframes
                return key_maps_dict["Constraint Keyframes"]
            else:
                key_maps_dict["Constraint Keyframes"] = []

        else:
            # 'AutoTrack' コンストレインが見つからなかった場合
            key_maps_dict["Constraint Keyframes"] = []

        return key_maps_dict["Constraint Keyframes"]
    
    def make_key_maps(self, obj, include_all=True, threshold=10):
        key_maps_dict={}
        scene = bpy.context.scene
        threshold = scene.keymapframe_maker.threshold
        # オブジェクトがない場合
        if not obj:
            return {None: {}}

        # アニメーションデータまたはアクションが存在しない場合のチェック
        if not obj.animation_data or not obj.animation_data.action:
            return {obj.name: {}}
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

        key_maps_dict["Constraint Keyframes"] = self.make_constant_dict(obj, key_maps_dict)

        # Find matching frames
        all_keyframes = key_maps_dict["All Keyframes"]
        constraint_keyframes = key_maps_dict["Constraint Keyframes"]
        matching_keyframes = sorted(set(all_keyframes) & set(constraint_keyframes))
        key_maps_dict["Matching Keyframes"] = matching_keyframes

        # Create a dictionary with the object name as the top-level key
        result = {obj.name: key_maps_dict}
        return result
# Operator to move between keyframes
class KYSYNKFM_OT_move_keyframe(bpy.types.Operator):
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
        
        key_maps_dict = MakeKeyMaps().make_key_maps(obj)
        # all_keyframes = key_maps_dict.get("All Keyframes", [])
        all_keyframes = key_maps_dict.get(obj.name, {}).get("All Keyframes", [])

        
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
class KYSYNKFM_OT_delete_keyframe(bpy.types.Operator):
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

class KYSYNKFM_OT_animated_playback(bpy.types.Operator):
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
# プレファレンス画面を開くオペレーターの定義
class KYSYNKFM_OP_OpenAddonPreferencesOperator(Operator):
    bl_idname = "ksynkfmpreferences.open_my_addon_prefs"
    bl_label = "Open Addon Preferences"

    def execute(self, context):
        bpy.ops.screen.userpref_show('INVOKE_DEFAULT')
        bpy.context.preferences.active_section = 'ADDONS'
        addon = bpy.context.preferences.addons[__name__]
        bpy.ops.preferences.addon_expand(module=addon.module)
        bpy.ops.preferences.addon_show(module = addon.module)

        return {'FINISHED'}

class KYSYNKFM_OP_JumpToFrame(bpy.types.Operator):
    bl_idname = "scene.jump_to_frame"
    bl_label = "Jump to Frame"
    bl_options = {'REGISTER', 'UNDO'}
    
    frame: bpy.props.IntProperty(name="Frame", default=1, min=1) # type: ignore
    
    def execute(self, context):
        # 指定されたフレームにジャンプ
        context.scene.frame_set(self.frame)
        return {'FINISHED'}
# アドオンプレファレンスの定義
class KYSYNKFM_AP_AddonPreferences(AddonPreferences):
    bl_idname = __name__

    category_keyframe: StringProperty(
        name="Keyframe Panel Category",
        description="Choose a name for the category of the Keyframe panel",
        default="KSYN",
        update=lambda self, context: PanelUpdateCategory().update_panel_category(self, context)
    ) # type: ignore
    category_keyframes: StringProperty(
        name="Keyframes Panel Category",
        description="Choose a name for the category of the Keyframes panel",
        default="KSYN",
        update=lambda self, context: PanelUpdateCategory().update_panel_category(self, context)
    ) # type: ignore
    category_playback: StringProperty(
        name="Animated Playback Panel Category",
        description="Choose a name for the category of the Animated Playback panel",
        default="KSYN",
        update=lambda self, context: PanelUpdateCategory().update_panel_category(self, context)
    ) # type: ignore
    category_fcurvepath: StringProperty(
        name="Fcurve Path Panel Category",
        description="Choose a name for the category of the Fcurve Path Panel",
        default="KSYN",
        update=lambda self, context: PanelUpdateCategory().update_panel_category(self, context)
    ) # type: ignore

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "category_keyframe")
        layout.prop(self, "category_keyframes")
        layout.prop(self, "category_playback")
        layout.prop(self, "category_fcurvepath")

class LayoutLabel:
    def calculate_differences(self, current_frame, previous_keyframe, next_keyframe):
        if current_frame is not None and previous_keyframe is not None:
            prev_difference = current_frame - previous_keyframe
        else:
            prev_difference = None  # Set appropriate default value if needed

        if current_frame is not None and next_keyframe is not None:
            next_difference = next_keyframe - current_frame
        else:
            next_difference = None  # Set appropriate default value if needed

        return prev_difference, next_difference
    # リストの左と右とマッチするのを検出する際にしよう
    def create_matching_list(self, objects):
        def get_all_keyframes(key_maps_dict, obj_name):
            return key_maps_dict.get(obj_name, {}).get("All Keyframes", [])

        # 各オブジェクトの全キーフレームを取得
        key_maps_dict = {}
        
        for obj in objects:
            # リストの中にオブジェクトがNoneの場合
            if obj==None:
                return key_maps_dict

            key_maps_dict[obj.name] = MakeKeyMaps().make_key_maps(obj).get(obj.name, {})

        # 最初のオブジェクトのキーフレームリストを基準に
        base_keyframes = set(get_all_keyframes(key_maps_dict, objects[0].name))
        
        # 他のオブジェクトと比較
        for obj in objects[1:]:
            obj_keyframes = set(get_all_keyframes(key_maps_dict, obj.name))
            base_keyframes &= obj_keyframes
        
        return sorted(base_keyframes)
    
    def layout_label(self, layout):
        layout.label(text="Keyframes:")

        include_all = bpy.context.scene.keymapframe_maker.include_all

        obj = bpy.context.scene.keymapframe_maker.key_f_target_object
        # Get keyframe data
    
        blank_icon = 'BLANK1'  # 空白用のアイコン
        unified_transform_icon = 'OUTLINER_OB_EMPTY'  # 統一アイコンとして使用するアイコン


        main_row = layout.row(align=True)
        objlist = [obj, bpy.context.object]
        obj_key_matchinlist=self.create_matching_list(objlist)

        for obj in objlist:
            # オブジェクトがNone場合はキーマップリストをスキップする。
            if not obj:
                continue
            def prev_label(layout, prev):
                layout.label(text=f"    {prev}", icon='SORT_DESC')
                
            def next_label(layout, next_):
                layout.label(text=f"    {next_}", icon='SORT_ASC')

                

            key_maps_dict = MakeKeyMaps().make_key_maps(obj, include_all=include_all)
            # print("###key_maps_dict",key_maps_dict)
            
            all_keyframes = key_maps_dict.get(obj.name, {}).get("All Keyframes", [])
            
            # if not all_keyframes:
            #     return

            previous_keyframe, next_keyframe, current_frame = self.create_keymap_list(all_keyframes)
            matching_keyframes = key_maps_dict.get(obj.name, {}).get("Matching Keyframes", [])
            location_keyframes = key_maps_dict.get(obj.name, {}).get("Location Keyframes", [])
            rotation_keyframes = key_maps_dict.get(obj.name, {}).get("Rotation_euler Keyframes", [])
            scale_keyframes = key_maps_dict.get(obj.name, {}).get("Scale Keyframes", [])
        
            column = main_row.column(align=True)
            obj_status= "Target" if obj == bpy.context.scene.keymapframe_maker.key_f_target_object else "Select"
            column.label(text = f"{obj.name} ({obj_status})", icon='OBJECT_DATA')


            # キーフレームボックス1
            box1 = column.box()
            col1 = box1.column(align=True)

            # キーフレームを表示
            for frame in all_keyframes:
                prev, next_ = self.calculate_differences(current_frame, previous_keyframe, next_keyframe)

                if frame == current_frame:
                    prev_label(col1, prev)
                    row = col1.row(align=True)
                    row.label(text=f" {frame}", icon='DECORATE_KEYFRAME')
                    row.label(text="", icon="CON_TRACKTO" if frame in matching_keyframes else blank_icon)
                    if frame in location_keyframes or frame in rotation_keyframes or frame in scale_keyframes:
                        row.label(text="", icon=unified_transform_icon)
                    else:
                        row.label(text="", icon=blank_icon)
                        
                    if frame in obj_key_matchinlist:
                        row.label(text=f"", icon='CHECKMARK')
                    else:
                        row.label(text="", icon=blank_icon)
                    next_label(col1, next_)
                    op = row.operator("scene.jump_to_frame", text="", icon='TIME')
                    op.frame = int(frame)

                else:
                    row = col1.row(align=True)
                    row.label(text=f" {frame}", icon='KEYFRAME')
                    row.label(text="", icon="CON_TRACKTO" if frame in matching_keyframes else blank_icon)
                    if frame in location_keyframes or frame in rotation_keyframes or frame in scale_keyframes:
                        row.label(text="", icon=unified_transform_icon)
                    else:
                        row.label(text="", icon=blank_icon)
                    if frame in obj_key_matchinlist:
                        row.label(text=f"", icon='CHECKMARK')
                    else:
                        row.label(text="", icon=blank_icon)
                    op = row.operator("scene.jump_to_frame", text="", icon='TIME')
                    op.frame = int(frame)

                if current_frame not in all_keyframes:
                    if frame == previous_keyframe:
                        prev_label(col1, prev)
                        row = col1.row(align=True)
                        row.label(text=f"    {current_frame}", icon='RIGHTARROW')
                        next_label(col1, next_)
            
            if obj is not None and obj.animation_data and obj.animation_data.action:
                pass
            else:
                col1.label(text=f"{obj.name} Not Anime Data:")

    def create_keymap_list(self, keyframe_points):
        
        scene = bpy.context.scene
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
# Define the panel
class KYSYNKFM_PT_keyframeInserter(bpy.types.Panel):
    bl_label = "Keyframe Inserter"
    bl_idname = "KYSYNKFM_PT_keyframeInserter"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'KSYN'


    def draw_header(self, context):
        layout = self.layout
        layout.label(icon='DECORATE_KEYFRAME')  # Specify the icon
        KYSYNKFM_PT_AnimatedPlaybackPanel.play_icon(context,layout)
        layout.operator(KYSYNKFM_OP_OpenAddonPreferencesOperator.bl_idname,text="",icon="TOOL_SETTINGS")


    def draw_constrains_elect(self, context):
        layout = self.layout
        scene=context.scene
        constraints_prop=scene.keymapframe_maker.constraints_props

        row = layout.row()
        col1 = row.column()
        col2 = row.column()
        def get_constraint_name(constraints_items, index):
            
            # constraints と constraints_select が空でないか、インデックスが範囲内であることを確認
            if 0 <= index < len(constraints_items):
                constraint_name = constraints_items[index].name
            else:
                #Noneを返すとgetでバグるので仕方なく空白にする
                constraint_name = ""
        
            return constraint_name
        
        objs_dict={
                    "KEY1":{
                    "obj":context.scene.keymapframe_maker.key_f_target_object,
                    "col":col1,
                    "list_props":constraints_prop,
                    "list":"constraints",
                    "list_index":"constraints_index",
                    "target_constraint" : get_constraint_name(constraints_prop.constraints, constraints_prop.constraints_index),
                    "status":"Target"

,
                        },
                    "KEY2":{
                    "obj":context.object,
                    "col":col2,
                    "list_props":constraints_prop,
                    "list":"constraints_select",
                    "list_index":"constraints_select_index",
                    "target_constraint" :get_constraint_name(constraints_prop.constraints_select, constraints_prop.constraints_select_index),
                    "status":"Select"
,
                        },
                }
        
        
        for key,item in objs_dict.items():
            # print("###item[]",item["obj"])
            #　ターゲットプロパティに何も選択してない場合
            if item["obj"]==None:
                continue
            item["col"].label(text=f"{item['obj'].name} ({item['status']} constraints.",icon="CONSTRAINT")
            if item["obj"].constraints:
                if item["obj"]:
                    item["col"].template_list("KYNKFM_UL_ConstrainList", item["list"], item["list_props"], item["list"], item["list_props"], item["list_index"])

                    # 選択されたコンストレイントの名前を表示
                    target_constraint =  item["target_constraint"]
                    
                    if target_constraint != "":
                        # print("###",target_constraint)
                        constraint = item["obj"].constraints.get(target_constraint)
                        if constraint:
                            item["col"].label(text=f"Constraint Name: {constraint.name}")
                            item["col"].label(text=f"Constraint Type: {constraint.type}")
        
                    else:
                        item["col"].label(text="No constraints available.Or, Select Constrain")
                else:
                    item["col"].label(text="No object selected.")

                
                if item["obj"] is not None and target_constraint in item["obj"].constraints:
                    constraint = item["obj"].constraints[target_constraint]
                    item["col"].label(text=f"This is the display of {target_constraint} Constraint")
                    item["col"].prop(constraint, "enabled")
                    item["col"].prop(constraint, "influence")
                    if constraint.type=="FOLLOW_PATH":
                        item["col"].prop(constraint, "offset")

                else:
                    item["col"].label(text=f"No {target_constraint} constraint found.")

            else:
                item["col"].label(text=f"No {item['obj'].name} constraint found.")


    def draw_framerate(self, layout, rd):
        col = layout.column(align=True)
        col.prop(rd, "fps")
        col.prop(rd, "fps_base", text="Base")
             

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        # rd = context.scene.render
        
        layout.prop(scene.keymapframe_maker, "key_f_target_object")
        row = layout.row(align=True)
        row.operator(KYSYNKFM_OT_insert_keyframe.bl_idname, icon='KEY_HLT', text="Insert Key")
        row.operator(KYSYNKFM_OT_insert_keyframe.bl_idname, icon='KEY_DEHLT', text="Delete Key")
        
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
        # view = context.space_data
        # row = layout.row(align=True)
        
        # row.prop(view, "lock_camera", text="Camera to View")
        props = scene.keymapframe_maker

        row = layout.row()
        icon = 'DOWNARROW_HLT' if props.show_draw_constraint else 'RIGHTARROW'
        row.prop(props, "show_draw_constraint", text="", icon=icon, emboss=False)
        row.label(text="Show Constraint")
        if props.show_draw_constraint:
            self.draw_constrains_elect(context)
            # self.draw_constraint(context)

    # def draw_constraint(self, context):
# Define the Keyframes panel
class KYSYNKFM_PT_keyframes_panel(bpy.types.Panel):
    bl_label = "Keyframes"
    bl_idname = "KYSYNKFM_PT_keyframes_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'KSYN'
    
    def draw_header(self, context):
        layout = self.layout
        layout.label(icon='DECORATE_KEYFRAME')  # Specify the icon
        KYSYNKFM_PT_AnimatedPlaybackPanel.play_icon(context,layout)

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        layout.prop(scene.keymapframe_maker, "include_all")
        if not scene.keymapframe_maker.include_all:
            layout.prop(scene.keymapframe_maker, "threshold")

        LayoutLabel().layout_label(layout)
# パネルの定義
class KYSYNKFM_PT_AnimatedPlaybackPanel(bpy.types.Panel):
    bl_label = "Keyframes Animation Control"
    bl_idname = "OBJECT_PT_keyframes_animated_playback_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'KSYN'

    @classmethod
    def play_icon(cls,context,layout):
        props = context.scene.keymapframe_maker
        if props.operator_status == "Running" and props.direction == "FORWARD":
            paly_icon='PAUSE'
            layout.label(text="",icon="PLAY")
        elif props.operator_status == "Running" and props.direction == "BACKWARD":
            paly_icon='PAUSE'
            layout.label(text="",icon="PLAY_REVERSE")

        else:
            paly_icon='PLAY'
            layout.operator(KYSYNKFM_OT_animated_playback.bl_idname,icon=paly_icon,text="")
            


    def draw_header(self, context):
        
        layout = self.layout
        layout.label(icon='DECORATE_KEYFRAME')  # Specify the icon
        self.play_icon(context,layout)



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
# カスタムUIリストの定義
class KYSYNKFM_UL_FCurveList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.label(text=item.name)

class KYSYNKFM_PT_FCurvePathsPanel(bpy.types.Panel):
    bl_label = "F-Curve Paths"
    bl_idname = "OBJECT_PT_fcurve_paths_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'KEY'

    def draw_header(self, context):
        layout = self.layout
        layout.label(icon='DECORATE_KEYFRAME')  # Specify the icon
        KYSYNKFM_PT_AnimatedPlaybackPanel.play_icon(context,layout)




    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.keymapframe_maker.anime_fcurves_props
        current_frame = scene.frame_current  # 現在のフレームを取得

        row = layout.row()
        col1 = row.column()
        col2 = row.column()
        
        
        obj =context.scene.keymapframe_maker.key_f_target_object


        object_data={"KEY1":{"obj":context.scene.keymapframe_maker.key_f_target_object,
                          "col":col1,
                          "curves":props.select_fcurves,
                          "list_fcurves":"select_fcurves",
                          "list_fcurves_index":"select_index",
                          "index" : props.select_index,
                                                   },
                    "KEY2":{"obj":context.active_object,
                          "col":col2,
                          "curves":props.active_fcurves,
                          "list_fcurves":"active_fcurves",
                          "list_fcurves_index":"active_index",
                          "index" : props.active_index,
                                                   },
                    }
        for key,item in object_data.items():

            col1=item["col"]
            obj=item["obj"]
            list_fcurves=item["list_fcurves"]
            list_fcurves_index=item["list_fcurves_index"]
            if  obj:



                col1.label(text=f"{obj.name}(Target) Object F-Curves:",icon="FCURVE")
                col1.template_list(
                    "KYSYNKFM_UL_FCurveList",
                    list_fcurves,
                    props,
                    list_fcurves,
                    props,
                    list_fcurves_index
                )
                        # キーフレームボックス1
                box1 = col1.box()
                col1 = box1.column(align=True)
                # アクティブオブジェクトのキーフレーム一覧
                if item["index"] >= 0 and item["index"] < len(item["curves"]):
                    fcurve_path = item["curves"][item["index"]].name
                    col1.label(text=f"{fcurve_path} F-Curve Keyframes:",icon="ACTION")
                    if obj and obj.animation_data and fcurve_path != "None":
                        fcurve = obj.animation_data.action.fcurves.find(fcurve_path)
                        if fcurve:
                            for kp in fcurve.keyframe_points:
                                icon = "KEYFRAME_HLT" if kp.co[0] == current_frame else "KEYFRAME"
                                row = col1.row(align=True)
                                # box=row.box()
                                row.label(text=f"{int(kp.co[0])}:  {kp.co[1]}",icon=icon)
                                op = row.operator("scene.jump_to_frame", text="", icon='TIME')
                                op.frame = int(kp.co[0])
# UIリストの定義
class KYNKFM_UL_ConstrainList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.label(text=f"{item.name}")
            layout.label(text=f"{item.type}")
# パネルのカテゴリーの自動変更機構
class PanelUpdateCategory:
    category_panels = [
            (KYSYNKFM_PT_AnimatedPlaybackPanel, "category_playback"),
            (KYSYNKFM_PT_keyframeInserter, "category_keyframe"),
            (KYSYNKFM_PT_keyframes_panel, "category_keyframes"),
            (KYSYNKFM_PT_FCurvePathsPanel, "category_fcurvepath"),
        ]
    
        
    def update_panel_category(self, dummy, context):
        self.register_category_panels()
    

    def register_category_panels(self):


        addon_prefs = bpy.context.preferences.addons[__name__].preferences

        for panel, category_attr in self.category_panels:
            try:
                bpy.utils.unregister_class(panel)
            except:
                pass

            panel.bl_category = getattr(addon_prefs, category_attr)
            bpy.utils.register_class(panel)

    def unregister_category_panels(self):


        for panel, category_attr in self.category_panels:
            # print("### un register panel",panel)
            bpy.utils.unregister_class(panel)
#　登録パネルとプロパティクラス以外のクラスのリスト
classes = [
    KYSYNKFM_OT_insert_keyframe,
    KYSYNKFM_OT_animated_playback,
    KYSYNKFM_OT_move_keyframe,
    KYSYNKFM_OT_delete_keyframe,
    KYSYNKFM_AP_AddonPreferences,
    KYSYNKFM_OP_OpenAddonPreferencesOperator,
    KYSYNKFM_UL_FCurveList,
    KYSYNKFM_OP_JumpToFrame,
    KYNKFM_UL_ConstrainList,
]
# Function to register properties and operators
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    RegisterProperties().register_properties()
    PanelUpdateCategory().register_category_panels()
# Function to unregister properties and operators
def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    RegisterProperties().unregister_properties()
    PanelUpdateCategory().unregister_category_panels()
# Execute the registration
if __name__ == "__main__":
    register()
