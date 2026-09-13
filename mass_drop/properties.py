from bpy.types import Operator, Panel, PropertyGroup, Object
from bpy.props import StringProperty, FloatProperty, CollectionProperty, IntProperty, PointerProperty, EnumProperty, BoolProperty
from .utils import on_toggle_projection

class CenterOfMassProperties(PropertyGroup):
    is_enabled: BoolProperty(
        name="Show Projection Line",
        description="Toggle real-time projection line",
        default=False,
        update=on_toggle_projection
    )
    density: FloatProperty(
        name="Material Density",
        default=1.0,
        min=0.01
    )

class AdvancedMassListItem(PropertyGroup):
    obj: PointerProperty(name="Object", type=Object)
    
    # Переключатель режима: Масса, Плотность
    input_mode: EnumProperty(
        name="Mode",
        items=[
            ('MASS', "Mass", "Enter mass directly", 'PHYSICS', 0),
            ('DENSITY', "Density", "Enter density manually", 'NODE_MATERIAL', 1)
        ],
        default='DENSITY'
    )
    
    # Поля для хранения данных
    mass: FloatProperty(name="Mass", default=1.0, min=0.0)
    density: FloatProperty(name="Density", default=1.0, min=0.0)


classes = (
    CenterOfMassProperties,
    AdvancedMassListItem,
)