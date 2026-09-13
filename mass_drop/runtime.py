"""Разделяемое состояние аддона на время выполнения.

Модуль ничего не импортирует из аддона, чтобы не создавать
циклических импортов. Наружу — только функции-аксессоры.
"""

_runtime_cache = {
    "batch": None,        # GPU batch для линии проекции
    "draw_handle": None,  # handle от SpaceView3D.draw_handler_add
    "last_com": None,     # последний посчитанный COM (Vector)
}

_com_cache: dict = {}


# --- GPU / проекция ---

def get_cache() -> dict:
    return _runtime_cache

def reset_projection_cache() -> None:
    _runtime_cache["batch"] = None
    _runtime_cache["last_com"] = None

def set_draw_handle(handle) -> None:
    _runtime_cache["draw_handle"] = handle

def get_draw_handle():
    return _runtime_cache["draw_handle"]


# --- Кэш локальных COM'ов ---

def get_cached_com(name: str):
    return _com_cache.get(name)

def set_cached_com(name: str, value) -> None:
    _com_cache[name] = value

def invalidate_com(name: str) -> None:
    _com_cache.pop(name, None)

def clear_com_cache() -> None:
    _com_cache.clear()