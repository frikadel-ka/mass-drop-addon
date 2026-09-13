import bpy
from bpy.app.handlers import persistent
from . import runtime
from .utils import redraw_ui


_cleaning = False  # защита от рекурсии, приватно для этого модуля


@persistent
def update_positions(scene, depsgraph):
    """Сбрасывает кэш COM при изменении геометрии отслеживаемых объектов."""
    # Ничего не делаем если кнопка выключена или сцены нет
    if scene is None or not hasattr(scene, "center_mass_props"):
        return
    if not scene.center_mass_props.is_enabled:
        return
    # Список имен объектов из adv_mass_list
    tracked_names = {item.obj.name for item in scene.adv_mass_list if item.obj}

    # Если в сцене изменилась геометрия объекта то имя объекта удалится из _com_cach соотв линия перестроится
    for update in depsgraph.updates:
        uid = update.id
        if hasattr(uid, "original") and uid.original is not None:
            uid = uid.original
        if isinstance(uid, bpy.types.Object) and uid.name in tracked_names:
            if update.is_updated_geometry or update.is_updated_transform:
                runtime.invalidate_com(uid.name)
                runtime.invalidate_vol((uid.name, uid.data.name))


@persistent
def _clean_adv_mass_list(scene, depsgraph=None):
    """Удаляет из списка элементы, чьи объекты больше не в сцене."""
    global _cleaning
    if _cleaning:
        return
    if scene is None or not hasattr(scene, "adv_mass_list"):
        return

    _cleaning = True
    try:
        # Проверяет наличие объектов из adv_mass_list в сцене и при ненаходе удаляет из списка
        lst = scene.adv_mass_list
        scene_obj_names = set(scene.objects.keys())
        removed = False
        for i in range(len(lst) - 1, -1, -1):
            obj = lst[i].obj
            if obj is None or obj.name not in scene_obj_names:
                lst.remove(i)
                removed = True
        if removed:
            n = len(lst)
            scene.adv_mass_list_index = 0 if n == 0 else min(scene.adv_mass_list_index, n - 1)
            redraw_ui()
    finally:
        _cleaning = False


def register():
    h = bpy.app.handlers.depsgraph_update_post
    if update_positions not in h:
        h.append(update_positions)
    if _clean_adv_mass_list not in h:
        h.append(_clean_adv_mass_list)


def unregister():
    h = bpy.app.handlers.depsgraph_update_post
    if _clean_adv_mass_list in h:
        h.remove(_clean_adv_mass_list)
    if update_positions in h:
        h.remove(update_positions)