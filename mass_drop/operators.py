import bpy
from bpy.types import Operator
from mathutils import Vector
from . import runtime
from .utils import total_loc, redraw_ui

# 3. Кнопка импорта объектов
class WM_OT_populate_advanced_list(Operator):
    bl_idname = "wm.populate_advanced_list"
    bl_label = "Import Selected Objects"

    def execute(self, context):
        context.scene.adv_mass_list.clear()
        for obj in context.selected_objects:
            item = context.scene.adv_mass_list.add()
            item.obj = obj
            if obj.rigid_body:
                item.mass = obj.rigid_body.mass
        return {'FINISHED'}

# Функция для вычисления объема с учетом модификаторов

# 4. Кнопка умного расчета центра масс
class WM_OT_calculate_advanced_com(Operator):
    bl_idname = "wm.calculate_advanced_com"
    bl_label = "Calculate Center of Mass"
    
    def execute(self, context):
        com = total_loc()
        if isinstance(com, Vector):
            context.scene.cursor.location = com
            runtime.reset_projection_cache()
            redraw_ui()
        return {'FINISHED'}

class WM_OT_add_objects(Operator):
    """Добавить новые выделенные объекты"""
    bl_idname = "wm.add_objects"
    bl_label = "Add Objects"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        added = 0
        skipped = []
        for obj in context.selected_objects:
            already_added = any(item.obj == obj for item in context.scene.adv_mass_list)
            if already_added:
                skipped.append(obj.name)
                continue
            item = context.scene.adv_mass_list.add()
            item.obj = obj
            if obj.rigid_body:
                item.mass = obj.rigid_body.mass
            added += 1
        if skipped:
            self.report({'WARNING'}, f"Уже в списке: {skipped}")
        if added:
            self.report({'INFO'}, f"Добавлено объектов: {added}")
        return {'FINISHED'}

class WM_OT_remove_objects(bpy.types.Operator):
    """Удалить выбранный объект"""
    bl_idname = "wm.remove_object"
    bl_label = "Remove Object"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        # Кнопка будет активна только если в коллекции есть хотя бы один элемент
        return len(context.scene.adv_mass_list) > 0

    def execute(self, context):
        scene = context.scene
        index = scene.adv_mass_list_index
        # Удаляем активный элемент
        scene.adv_mass_list.remove(index)
        # Корректируем индекс, чтобы он не вышел за пределы массива после удаления
        scene.adv_mass_list_index = min(max(0, index - 1), len(scene.adv_mass_list) - 1)
        return {'FINISHED'}

classes = {
    WM_OT_populate_advanced_list,
    WM_OT_calculate_advanced_com,
    WM_OT_add_objects,
    WM_OT_remove_objects
}