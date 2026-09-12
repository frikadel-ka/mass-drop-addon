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
import bmesh
from mathutils import Matrix
from mathutils import Vector
import gpu
from gpu_extras.batch import batch_for_shader
#translations_dict = translations.translations_dict

# Кэш батчей только для текущей сессии
_runtime_cache = {
    "batch": None,
    "draw_handle": None
}

_com_cashe = {}

def draw_callback():
    # Получаем настройки из UI
    props = bpy.context.scene.center_mass_props
    if not props.is_enabled:
        return
        
    if _runtime_cache["batch"]:
        # Отрисовка батча...
        pass


# --- 1. ФУНКЦИЯ ОБНОВЛЕНИЯ КООРДИНАТ И БАТЧА ---
def update_positions(scene, depsgraph):
    need_recalc = False
    return # на время


    # Берем активный объект (не просто выделенный)
    # obj = bpy.context.active_object
    
    # # Если объект не выделен — очищаем батч и выходим
    # if not obj:
    #     _runtime_cache["batch"] = None
    #     return

    # # АКТУАЛЬНЫЙ ЦЕНТР: Мировые координаты Origin объекта
    # # (Позже подставишь сюда свой расчёт центра масс через bmesh)
    # center = obj.matrix_world.translation.copy()


    center = total_loc()
    
    # ПРОЕКЦИЯ: Для примера проецируем вниз на 2 units по оси Z
    #projection = center.copy()
    #projection.z -= 2.0
    # Таким же образом можно применять вектора, НО делать не фиксированным а по функции чтобы отрезки были не статичными
    
    # Или делаем статичным
    projection = (0.0,0.0,0.0)
    
    # ПЕРЕСОЗДАНИЕ БАТЧА (Старый батч заменяется новым, фантомных линий не будет)
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    coords = [center, projection]
    _runtime_cache["batch"] = batch_for_shader(shader, 'LINES', {"pos": coords})

def rebuild_projection_batch(context):
    scene = context.scene
    
    # Начало проекции в 3D курсоре
    cursor_loc = scene.cursor.location.copy()
    
    # Конец проекции — рассчитанный центр масс
    # (Вызываем total_loc() принудительно по кнопке/вызову)
    try:
        com_loc = total_loc()
    except Exception:
        com_loc = cursor_loc.copy()

    com_loc = total_loc()
        
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    coords = [(com_loc.x,com_loc.y,0.0), com_loc]
    _runtime_cache["batch"] = batch_for_shader(shader, 'LINES', {"pos": coords})
    
    # Принудительно обновляем отображение в окне 3D View
    if context.area:
        context.area.tag_redraw()

# --- 2. ФУНКЦИЯ GPU-ОТРИСОВКИ ---
def draw_callback():
    # Если батча нет -> не выполняем функию
    if not _runtime_cache["batch"]:
        return
        
    # Создаем линию
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    shader.bind()
    shader.uniform_float("color", (1.0, 0.0, 0.0, 1.0)) # Красный
    
    #gpu.state.line_width_set(3.0)
    _runtime_cache["batch"].draw(shader)
    gpu.state.line_width_set(3.0)

# ---Функции для находения центра объекта--- ПЕРЕДЕЛАТЬ!!! ЧТОБЫ СЧИТАЛО ПО ГЛОБАЛЬНЫМ КООРДИНАТАМ

def get_bmesh_volume_center(bm: bmesh.types.BMesh) -> Vector:
    """Возвращает точный центр масс замкнутого BMesh по его объёму."""
    total_volume = 0.0
    center_mass = Vector((0.0, 0.0, 0.0))
    
    # Для корректного расчёта разбиваем грани на треугольники
    # (операция выполняется над копией в памяти)
    bm_copy = bm.copy()
    bmesh.ops.triangulate(bm_copy, faces=bm_copy.faces)
    
    for face in bm_copy.faces:
        # Вершины треугольной грани
        v1, v2, v3 = [v.co for v in face.verts]
        
        # Ориентированный объём тетраэдра с вершиной в (0,0,0)
        signed_tri_vol = v1.dot(v2.cross(v3)) / 6.0
        
        # Центроид тетраэдра
        tri_centroid = (v1 + v2 + v3) / 4.0
        
        total_volume += signed_tri_vol
        center_mass += tri_centroid * signed_tri_vol
        print(total_volume)
        print(center_mass)
        
    bm_copy.free()
    
    if abs(total_volume) > 1e-6:
        return center_mass / total_volume
    
    # Если объём нулевой (сетка не замкнута), возвращаем среднее по граням
    return get_bmesh_surface_center(bm)

def get_bmesh_surface_center(bm: bmesh.types.BMesh) -> Vector:
    """Возвращает центроид BMesh, взвешенный по площади граней."""
    total_area = 0.0
    center_mass = Vector((0.0, 0.0, 0.0))
    
    for face in bm.faces:
        area = face.calc_area()
        # calc_center_median() — актуальный метод BMeshFace для центра грани
        center = face.calc_center_median()
        
        total_area += area
        center_mass += center * area
        
    if total_area > 0.0:
        return center_mass / total_area
        
    # Фоллбэк: если граней нет, считаем просто по вершинам
    if bm.verts:
        return sum((v.co for v in bm.verts), Vector()) / len(bm.verts)
        
    return Vector((0.0, 0.0, 0.0))

def set_origin_to_bmesh_center_of_mass(obj: bpy.types.Object):
    print(obj.type)
    if not obj or obj.type != 'MESH':
        return

    obj_world_loc = obj.matrix_world.to_translation()
    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)

    # Определяем, является ли сетка замкнутой (manifold)
    is_solid = all(len(e.link_faces) == 2 for e in bm.edges)
    print(is_solid)
    if is_solid:
        return get_bmesh_volume_center(bm) + obj_world_loc
    else:
        return get_bmesh_surface_center(bm) + obj_world_loc

def total_loc():
    scene = bpy.context.scene
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

        global_obj_loc = set_origin_to_bmesh_center_of_mass(item.obj)
        print(global_obj_loc)
            
        weighted_sum += global_obj_loc * final_mass #weighted_sum += item.obj.location * final_mass
        total_mass += final_mass
        
    if total_mass <= 0:
        self.report({'WARNING'}, "Total calculated mass is zero!")
        return {'CANCELLED'}
        
    com = weighted_sum / total_mass
    return com

# ---Функции отрисовки линии и проекции--- (пока только линий)
class CenterOfMassProperties(PropertyGroup):
    is_enabled: bpy.props.BoolProperty(
        name="Show Center of Mass",
        default=False,
        update=lambda self, context: context.area.tag_redraw()
    )
    density: bpy.props.FloatProperty(
        name="Material Density",
        default=1.0,
        min=0.01
    )

# Регистрация свойства в сцену (в register()):
# bpy.types.Scene.center_mass_props = bpy.props.PointerProperty(type=CenterOfMassProperties)
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
        com = total_loc()
        if isinstance(com, Vector):
            context.scene.cursor.location = com
            # Перестраиваем линию от 3D курсора к центру масс для отладки
            rebuild_projection_batch(context)
        #self.report({'INFO'}, f"COM: ({com.x:.3f}, {com.y:.3f}, {com.z:.3f}). Cursor moved.")
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
    CenterOfMassProperties,
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
    bpy.types.Scene.adv_mass_list_index = bpy.props.IntProperty(name="Index for adv_mass_list", default=0)

    bpy.types.Scene.center_mass_props = bpy.props.PointerProperty(type=CenterOfMassProperties)
    
    # Регистрируем постоянный обработчик
    _runtime_cache["draw_handle"] = bpy.types.SpaceView3D.draw_handler_add(
        draw_callback, (), 'WINDOW', 'POST_VIEW'
    )
    bpy.app.handlers.depsgraph_update_post.append(update_positions)

    #bpy.app.translations.register(__name__, translations_dict)

def unregister():
    if _runtime_cache["draw_handle"]:
        bpy.types.SpaceView3D.draw_handler_remove(_runtime_cache["draw_handle"], 'WINDOW')
        _runtime_cache["draw_handle"] = None
        
    if update_positions in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(update_positions)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.center_mass_props

    del bpy.types.Scene.adv_mass_list

    del bpy.types.Scene.adv_mass_list_index

    #bpy.app.translations.unregister(__name__)

if __name__ == "__main__":
    register()