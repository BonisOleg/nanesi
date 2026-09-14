"""Сітка карток товарів: pick_grid_columns (product-grid skill)."""
from django import template

register = template.Library()


def pick_grid_columns(count: int, *, mobile: bool = False) -> int:
    """Десктоп: 4/3; мобільна: завжди 2. Без одиночної картки в останньому ряді."""
    if mobile or count <= 0:
        return 2
    if count <= 2:
        return 3

    for cols in (4, 3):
        if count % cols == 0:
            return cols

    for cols in (4, 3):
        if count % cols >= 3:
            return cols

    for cols in (4, 3):
        if count % cols == 2:
            return cols

    return 3


@register.filter(name="pick_grid_columns")
def pick_grid_columns_filter(count) -> int:
    try:
        value = int(count)
    except (TypeError, ValueError):
        return 3
    return pick_grid_columns(value)
