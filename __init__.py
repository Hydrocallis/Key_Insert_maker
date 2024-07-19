bl_info = {
    "name": "Keyframe Tools",
    "blender": (4, 2, 0),
    "category": "Object",
    "version": (1, 0, 0),
    "author": "KSYN",
    "description": "A set of tools for inserting, deleting, and moving keyframes.",
    "location": "View3D > UI > Keyframe Tools",
    "warning": "",
    "doc_url": "",
    "tracker_url": "",
    "support": "COMMUNITY"
}

import bpy

# シーンプロパティにポインタープロパティを追加
def register_properties():
    bpy.types.Scene.key_f_target_object = bpy.props.PointerProperty(
        name="Target Object",
        type=bpy.types.Object,
        description="キーフレームを挿入する対象のオブジェクト"
    )

# キーフレームを挿入するオペレーター
class OBJECT_OT_insert_keyframe(bpy.types.Operator):
    bl_idname = "object.insert_keyframe"
    bl_label = "Insert Keyframe"
    bl_description = "指定したオブジェクトに現在のフレームでキーフレームを挿入"
    
    def execute(self, context):
        scene = context.scene
        obj = scene.key_f_target_object
        
        if obj is None:
            self.report({'WARNING'}, "ターゲットオブジェクトが設定されていません。")
            return {'CANCELLED'}
        
        current_frame = scene.frame_current
        properties = ['location', 'rotation_euler', 'scale']
        
        for prop in properties:
            obj.keyframe_insert(data_path=prop, frame=current_frame)
        
        self.report({'INFO'}, f"オブジェクト '{obj.name}' にフレーム {current_frame} でキーフレームを挿入しました。")
        return {'FINISHED'}
    

# キーフレーム間を移動するオペレーター
class OBJECT_OT_move_keyframe(bpy.types.Operator):
    bl_idname = "object.move_keyframe"
    bl_label = "Move Keyframe"
    bl_description = "指定したオブジェクトのキーフレーム間を移動"
    
    direction: bpy.props.EnumProperty(
        name="Direction",
        description="キーフレームの移動方向を指定",
        items=[
            ('PREVIOUS', "Previous", "前のキーフレームに移動"),
            ('NEXT', "Next", "次のキーフレームに移動"),
            ('FIRST', "First", "最初のキーフレームに移動"),
            ('LAST', "Last", "最後のキーフレームに移動")
        ]
    ) # type: ignore

    
    
    def execute(self, context):
        scene = context.scene
        obj = scene.key_f_target_object
        
        if obj is None:
            self.report({'WARNING'}, "ターゲットオブジェクトが設定されていません。")
            return {'CANCELLED'}
        
        current_frame = scene.frame_current
        keyframe_points = sorted({kp.co[0] for fcu in obj.animation_data.action.fcurves for kp in fcu.keyframe_points})
        
        if not keyframe_points:
            self.report({'INFO'}, "キーフレームがありません。")
            return {'CANCELLED'}
        
        if self.direction == 'PREVIOUS':
            previous_keyframes = [kf for kf in keyframe_points if kf < current_frame]
            if previous_keyframes:
                scene.frame_current = int(max(previous_keyframes))
            else:
                scene.frame_current = int(keyframe_points[-1])
            self.report({'INFO'}, f"フレーム {scene.frame_current} に移動しました。")
        elif self.direction == 'NEXT':
            next_keyframes = [kf for kf in keyframe_points if kf > current_frame]
            if next_keyframes:
                scene.frame_current = int(min(next_keyframes))
            else:
                scene.frame_current = int(keyframe_points[0])
            self.report({'INFO'}, f"フレーム {scene.frame_current} に移動しました。")
        elif self.direction == 'FIRST':
            scene.frame_current = int(keyframe_points[0])
            self.report({'INFO'}, f"最初のフレーム {scene.frame_current} に移動しました。")
        elif self.direction == 'LAST':
            scene.frame_current = int(keyframe_points[-1])
            self.report({'INFO'}, f"最後のフレーム {scene.frame_current} に移動しました。")
        
        return {'FINISHED'}

# 現在のキーフレームを削除するオペレーター
class OBJECT_OT_delete_keyframe(bpy.types.Operator):
    bl_idname = "object.delete_keyframe"
    bl_label = "Delete Keyframe"
    bl_description = "指定したオブジェクトの現在のフレームのキーフレームを削除"
    
    def execute(self, context):
        scene = context.scene
        obj = scene.key_f_target_object
        
        if obj is None:
            self.report({'WARNING'}, "ターゲットオブジェクトが設定されていません。")
            return {'CANCELLED'}
        
        current_frame = scene.frame_current
        properties = ['location', 'rotation_euler', 'scale']
        
        for prop in properties:
            obj.keyframe_delete(data_path=prop, frame=current_frame)
        
        self.report({'INFO'}, f"オブジェクト '{obj.name}' のフレーム {current_frame} のキーフレームを削除しました。")
        return {'FINISHED'}
    
def calculate_differences(current_frame, previous_keyframe, next_keyframe):
    if current_frame is not None and previous_keyframe is not None:
        prev_difference = current_frame - previous_keyframe
    else:
        prev_difference = None  # 必要に応じて適切な代替値を設定してください

    if current_frame is not None and next_keyframe is not None:
        next_difference = next_keyframe - current_frame
    else:
        next_difference = None  # 必要に応じて適切な代替値を設定してください

    return prev_difference, next_difference

def prev_labe(layout, prev):
    layout.label(text=f"    {prev}", icon='SORT_DESC')
    
def next_label(layout, next_):
    layout.label(text=f"    {next_}", icon='SORT_ASC')


def layout_label(layout,keyframe_points,current_frame,next_keyframe,previous_keyframe):
    for frame in keyframe_points:
        prev, next_ = calculate_differences(current_frame, previous_keyframe, next_keyframe)
                
        if frame == current_frame:

            prev_labe(layout, prev)
            layout.label(text=f" {frame}", icon='DECORATE_KEYFRAME')
            next_label(layout, next_)
                                
        else:
            layout.label(text=f"{frame}",icon="KEYFRAME")
            
        if not current_frame in keyframe_points:
            if frame == previous_keyframe:
                prev_labe(layout, prev)
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
    
    # next_keyframeが見つからなかった場合、再生レンダリング範囲の最後のフレームと比較する
    if next_keyframe is None:
        next_keyframe = scene.frame_end
    
    # previous_keyframeが見つからなかった場合、再生レンダリング範囲の最初のフレームと比較する
    if previous_keyframe is None:
        previous_keyframe = scene.frame_start
    
    return previous_keyframe, next_keyframe, current_frame

    

def draw_keyframes(layout, obj, scene):
    if obj is not None and obj.animation_data and obj.animation_data.action:
        layout.label(text="Keyframes:")
        keyframe_points = sorted({int(kp.co[0]) for fcu in obj.animation_data.action.fcurves for kp in fcu.keyframe_points})
        
        if not keyframe_points:
            return
        
        previous_keyframe,next_keyframe,current_frame = create_keymap_list(keyframe_points,scene)
            
        
        layout_label(layout,keyframe_points,current_frame,next_keyframe,previous_keyframe)


# パネルを定義
class OBJECT_PT_keyframe_panel(bpy.types.Panel):
    bl_label = "Keyframe Inserter"
    bl_idname = "OBJECT_PT_keyframe_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Keyframe Tools'
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        obj = scene.key_f_target_object
        
        layout.prop(scene, "key_f_target_object")

        
        row = layout.row(align=True)
        row.operator("object.insert_keyframe", icon='KEY_HLT',text="Insert Key")
        row.operator("object.delete_keyframe", icon='KEY_DEHLT',text="Delete Key")
        
        row = layout.row(align=True)
            
        row.operator("object.move_keyframe", text="", icon='PREV_KEYFRAME').direction = 'FIRST'
        row.separator(factor=2.0)  # 間隔を開ける
        row.operator("object.move_keyframe", text="", icon='TRIA_LEFT').direction = 'PREVIOUS'
        row.separator(factor=2.0)  # 間隔を開ける
        row.prop(scene, "frame_current", text="")
        row.separator(factor=2.0)  # 間隔を開ける
        row.operator("object.move_keyframe", text="", icon='TRIA_RIGHT').direction = 'NEXT'
        row.separator(factor=2.0)  # 間隔を開ける
        row.operator("object.move_keyframe", text="", icon='NEXT_KEYFRAME').direction = 'LAST'

# Keyframes パネルを定義
class OBJECT_PT_keyframes_panel(bpy.types.Panel):
    bl_label = "Keyframes"
    bl_idname = "OBJECT_PT_keyframes_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Keyframe Tools'
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        obj = scene.key_f_target_object
        
        draw_keyframes(layout, obj, scene)



# プロパティとオペレーターの登録関数
def register():
    register_properties()
    bpy.utils.register_class(OBJECT_OT_insert_keyframe)
    bpy.utils.register_class(OBJECT_OT_move_keyframe)
    bpy.utils.register_class(OBJECT_OT_delete_keyframe)
    bpy.utils.register_class(OBJECT_PT_keyframe_panel)
    bpy.utils.register_class(OBJECT_PT_keyframes_panel)

# プロパティとオペレーターの登録解除関数
def unregister():
    del bpy.types.Scene.key_f_target_object
    bpy.utils.unregister_class(OBJECT_OT_insert_keyframe)
    bpy.utils.unregister_class(OBJECT_OT_move_keyframe)
    bpy.utils.unregister_class(OBJECT_OT_delete_keyframe)
    bpy.utils.unregister_class(OBJECT_PT_keyframe_panel)
    bpy.utils.unregister_class(OBJECT_PT_keyframes_panel)

# 登録を実行
if __name__ == "__main__":
    register()
