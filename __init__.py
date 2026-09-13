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
-выделяешь объекты
-нажмаешь кнопку "Import Selected Object" или <Плюс> слева от списка чтобы сделать список с нуля или добавить соответственно
-нажав "Live Projection" включаешь или выключаешь вектор с проекцией
-редактируешь парамтры объектов, линии-вектора и проекцию в панели
'''


bl_info = {
    "name": "Mass Drop",
    "author": "Frikadel_ka",
    "description": "This add-on determines thr center of mass of objects and creates its projection.",
    "blender": (4, 3, 0),
    "version": (0, 0, 1),
    "location": "View3D > Sidebar > Mass Drop",
    "warning": "",
    "doc_url": "https://github.com/frikadel-ka/mass_drop-addon#readme",
    "tracker_url": "https://github.com/frikadel-ka/mass_drop-addon/issues",
    "category": "Object",
}

if "bpy" in locals():
    import importlib
    from .mass_drop import runtime, properties, utils, operators, ui, handlers
    importlib.reload(runtime)
    importlib.reload(properties)
    importlib.reload(utils)
    importlib.reload(operators)
    importlib.reload(ui)
    importlib.reload(handlers)
else:
    from .mass_drop import runtime, properties, utils, operators, ui, handlers

import bpy #type: ignore

classes = (
    *properties.classes,
    *operators.classes,
    *ui.classes,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.adv_mass_list = bpy.props.CollectionProperty(type=properties.AdvancedMassListItem)
    bpy.types.Scene.adv_mass_list_index = bpy.props.IntProperty(name="Index for adv_mass_list", default=0)
    bpy.types.Scene.center_mass_props = bpy.props.PointerProperty(type=properties.CenterOfMassProperties)

    handle = bpy.types.SpaceView3D.draw_handler_add(utils.draw_callback, (), 'WINDOW', 'POST_VIEW')
    runtime.set_draw_handle(handle)

    handlers.register()

def unregister():
    handlers.unregister()

    handle = runtime.get_draw_handle()
    if handle:
        bpy.types.SpaceView3D.draw_handler_remove(handle, 'WINDOW')
        runtime.set_draw_handle(None)

    runtime.clear_com_cache()
    runtime.reset_projection_cache()

    del bpy.types.Scene.center_mass_props
    del bpy.types.Scene.adv_mass_list
    del bpy.types.Scene.adv_mass_list_index

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()