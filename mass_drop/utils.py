import bpy
import gpu
from gpu_extras.batch import batch_for_shader
import bmesh
from mathutils import Vector

from . import runtime


def get_scene_obj_names(scene):
    return set(scene.objects.keys())


def redraw_ui():
    wm = bpy.context.window_manager
    if wm is None:
        return
    for window in wm.windows:
        screen = window.screen
        if screen is None:
            continue
        for area in screen.areas:
            if area.type in {'VIEW_3D', 'PROPERTIES', 'OUTLINER'}:
                area.tag_redraw()
        for region in screen.regions:
            region.tag_redraw()


def on_toggle_projection(self, context):
    runtime.reset_projection_cache()
    redraw_ui()


def draw_callback():
    if not bpy.context.scene.center_mass_props.is_enabled:
        return
    com_loc = total_loc()
    if com_loc is None:
        runtime.reset_projection_cache()
        return

    cache = runtime.get_cache()
    last = cache["last_com"]
    if last is None or (last - com_loc).length > 1e-6:
        shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        coords = [
            (com_loc.x, com_loc.y, 0.0),
            (com_loc.x, com_loc.y, com_loc.z),
        ]
        cache["batch"] = batch_for_shader(shader, 'LINES', {"pos": coords})
        cache["last_com"] = com_loc.copy()

    if not cache["batch"]:
        return
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    shader.bind()
    shader.uniform_float("color", (1.0, 0.0, 0.0, 1.0))
    gpu.state.line_width_set(3.0)
    cache["batch"].draw(shader)
    gpu.state.line_width_set(1.0)


def get_global_com(obj):
    if not obj or obj.type != 'MESH':
        return None
    local_com = runtime.get_cached_com(obj.name)
    if local_com is None:
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        is_solid = all(len(e.link_faces) == 2 for e in bm.edges)
        local_com = get_bmesh_volume_center(bm) if is_solid else get_bmesh_surface_center(bm)
        bm.free()
        runtime.set_cached_com(obj.name, local_com)
    return obj.matrix_world @ local_com

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

def total_loc():
    scene = bpy.context.scene
    total_mass = 0.0
    weighted_sum = Vector((0.0, 0.0, 0.0))
    
    for item in scene.adv_mass_list:
        if not item.obj:
            continue
            
        # 1. Расчет массы
        if item.input_mode == 'MASS':
            final_mass = item.mass
        elif item.input_mode == 'DENSITY':
            final_mass = get_obj_volume(item.obj) * item.density
        else:
            final_mass = 0.0

        # Игнорируем объекты без массы
        if final_mass <= 0:
            continue

        # 2. Быстрое получение центра из кэша (без замедлений bmesh)
        global_obj_loc = get_global_com(item.obj)
            
        weighted_sum += global_obj_loc * final_mass
        total_mass += final_mass
        
    # Если список пуст или суммарная масса = 0
    if total_mass <= 0:
        return None
        
    return weighted_sum / total_mass# ---Функции отрисовки линии и проекции--- (пока только линий)

