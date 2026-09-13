import bpy

class OBJECT_PT_advanced_mass_panel(bpy.types.Panel):
    bl_label = "Advanced Mass Center Calculator"
    bl_idname = "OBJECT_PT_advanced_mass_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Mass Drop Tools'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        # Кнопка-переключатель (включить/выключить проекцию)
        icon_state = 'HIDE_OFF' if scene.center_mass_props.is_enabled else 'HIDE_ON'
        layout.prop(scene.center_mass_props, "is_enabled", text="Live Projection", toggle=True, icon=icon_state)
        
        layout.separator()
        layout.operator("wm.populate_advanced_list", icon='ZOOM_ALL')
        layout.separator()
        
        if len(scene.adv_mass_list) == 0:
            layout.label(text="List empty. Select objects and import.")
            return

        row_header = layout.row()
        row_header.label(text="Object Name")
        row_header.label(text="Mode Selection")
        row_header.label(text="Value / Input")

        row = layout.row()
        col = row.column(align=True)
        col.operator("wm.add_objects", icon='ADD', text="")
        col.operator("wm.remove_object", icon='REMOVE', text="")
        
        row.template_list(
            "WM_UL_objects", "", 
            scene, "adv_mass_list", 
            scene, "adv_mass_list_index"
        )

class WM_UL_objects(bpy.types.UIList):
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
    OBJECT_PT_advanced_mass_panel,
    WM_UL_objects,
)