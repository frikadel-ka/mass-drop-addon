# Copyright (C) 2026 Frikadel_ka

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


'''
Аддон для создания проекции центра масс объектов

Функционал:
'''


bl_info = {
    "name": "Mass Drop",
    "author": "Frikadel_ka",
    "description": "This add-on determines thr center of mass of objects and creates its projection.",
    "blender": (4, 3, 0),
    "version": (0, 0, 1),
    "location": "View3D > Sidebar > Mass Drop",
    "warning": "",
    #"doc_url": "https://github.com/frikadel-ka/wheel-of-fortune-addon#readme",
    #"tracker_url": "https://github.com/frikadel-ka/wheel-of-fortune-addon/issues",
    "category": "Object",
}

from bpy.types import Operator, Panel, PropertyGroup, Object
from bpy.props import StringProperty, FloatProperty, CollectionProperty, IntProperty, PointerProperty, EnumProperty, BoolProperty # type: ignore

import bpy #type: ignore
from mathutils import Vector
#translations_dict = translations.translations_dict
class AdvancedMassListItem(PropertyGroup):
    obj: PointerProperty(name="Object", type=Object)
    
    # Переключатель режима: Масса, Плотность
    input_mode: EnumProperty(
        name="Mode",
        items=[
            ('MASS', "Mass", "Enter mass directly", 'PHYSICS', 0),
            ('DENSITY', "Density", "Enter density manually", 'NODE_MATERIAL', 1)
        ],
        default='MASS'
    )
    
    # Поля для хранения данных
    mass: FloatProperty(name="Mass", default=1.0, min=0.0)
    density: FloatProperty(name="Density", default=1.0, min=0.0)

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
def get_obj_volume(obj):
    try:
        depsgraph = bpy.context.evaluated_depsgraph_get()
        obj_eval = obj.evaluated_get(depsgraph)
        mesh_eval = obj_eval.to_mesh()
        volume = mesh_eval.calc_volume()
        obj_eval.to_mesh_clear()
        scale = obj.scale
        return volume * (scale.x * scale.y * scale.z)
    except:
        return 1.0 # Если у объекта нет геометрии (например, Empty)

# 4. Кнопка умного расчета центра масс
class WM_OT_calculate_advanced_com(Operator):
    bl_idname = "wm.calculate_advanced_com"
    bl_label = "Calculate Center of Mass"
    
    def execute(self, context):
        scene = context.scene
        total_mass = 0.0
        weighted_sum = Vector((0.0, 0.0, 0.0))
        
        for item in scene.adv_mass_list:
            if not item.obj:
                continue
                
            # Вычисляем финальную массу объекта в зависимости от выбранного режима
            final_mass = 0.0
            if item.input_mode == 'MASS':
                final_mass = item.mass
            elif item.input_mode == 'DENSITY':
                final_mass = get_obj_volume(item.obj) * item.density
                
            weighted_sum += item.obj.location * final_mass
            total_mass += final_mass
            
        if total_mass <= 0:
            self.report({'WARNING'}, "Total calculated mass is zero!")
            return {'CANCELLED'}
            
        com = weighted_sum / total_mass
        context.scene.cursor.location = com
        self.report({'INFO'}, f"COM: ({com.x:.3f}, {com.y:.3f}, {com.z:.3f}). Cursor moved.")
        return {'FINISHED'}

class WM_OT_add_objects(Operator):
    """Добавить новые выделенные объекты"""
    bl_idname = "wm.add_objects"
    bl_label = "Add Objects"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        for obj in context.selected_objects:
            item = context.scene.adv_mass_list.add()
            item.obj = obj
            if obj.rigid_body:
                item.mass = obj.rigid_body.mass
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
# 5. Отрисовка адаптивного интерфейса
class OBJECT_PT_advanced_mass_panel(Panel):
    bl_label = "Advanced Mass Center Calculator"
    bl_idname = "OBJECT_PT_advanced_mass_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Mass Drop Tools'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        layout.operator("wm.populate_advanced_list", icon='ZOOM_ALL')
        layout.separator()
        
        if len(scene.adv_mass_list) == 0:
            layout.label(text="List empty. Select objects and import.")
            return
            
        #box = layout.box()
        
        # Шапка таблицы для понятности
        row_header = layout.row()
        row_header.label(text="Object Name")
        row_header.label(text="Mode Selection")
        row_header.label(text="Value / Input")
        #layout.separator()

        row = layout.row()

        col = row.column(align=True)
        col.operator("wm.add_objects", icon='ADD', text="")
        col.operator("wm.remove_object", icon='REMOVE', text="")
                # Вызов списка в панели (замените ваш row.template_list)
        # Обязательно передаем scene и имя свойства-индекса в конце
        row.template_list(
            "WM_WL_objects", "", 
            scene, "adv_mass_list", 
            scene, "adv_mass_list_index"
        )

        layout.separator()
        layout.operator("wm.calculate_advanced_com", icon='PHYSICS')


class WM_WL_objects(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        # Отрисовка элемента списка. Используем переданный layout напрямую!
        if item.obj:
            # Создаем ровную строку. align=True склеит элементы в аккуратную полосу
            row = layout.row(align=True)
            
            # 1 колонка: имя объекта
            row.label(text=item.obj.name, icon='OBJECT_DATA')
            
            # 2 колонка: Выпадающий список выбора режима ввода
            row.prop(item, "input_mode", text="")
            
            # 3 колонка: Динамическое поле ввода
            if item.input_mode == 'MASS':
                row.prop(item, "mass", text="")
            elif item.input_mode == 'DENSITY':
                row.prop(item, "density", text="ρ")



classes = (
    AdvancedMassListItem, 
    WM_OT_populate_advanced_list, 
    WM_OT_calculate_advanced_com,
    WM_OT_add_objects,
    WM_OT_remove_objects,
    WM_WL_objects,
    OBJECT_PT_advanced_mass_panel
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.adv_mass_list = bpy.props.CollectionProperty(type=AdvancedMassListItem)
    # Вставьте это туда, где регистрируете свойства сцены (обычно в register())
    bpy.types.Scene.adv_mass_list_index = bpy.props.IntProperty(name="Index for adv_mass_list", default=0)

    #bpy.app.translations.register(__name__, translations_dict)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.adv_mass_list

    del bpy.types.Scene.adv_mass_list_index

    #bpy.app.translations.unregister(__name__)

if __name__ == "__main__":
    register()