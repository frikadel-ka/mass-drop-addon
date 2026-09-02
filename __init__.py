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
    "doc_url": "https://github.com/frikadel-ka/wheel-of-fortune-addon#readme",
    "tracker_url": "https://github.com/frikadel-ka/wheel-of-fortune-addon/issues",
    "category": "Object",
}


from bpy.props import StringProperty, FloatProperty, CollectionProperty, IntProperty, PointerProperty, EnumProperty, BoolProperty # type: ignore


if "bpy" in locals():
    import importlib
    # Вписываем сюда все ваши файлы, кроме init.py
    #translations=importlib.reload(translations)
    print("--- Аддон обновлен ---")
else:
    #from .mass_drop import translations


import bpy #type: ignore
#translations_dict = translations.translations_dict


classes = (
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    #bpy.app.translations.register(__name__, translations_dict)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    #bpy.app.translations.unregister(__name__)

if __name__ == "__main__":
    register()