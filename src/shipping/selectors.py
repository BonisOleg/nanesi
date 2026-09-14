"""Тільки читання — пошук міст/відділень ЛИШЕ з локальної БД (novaposhta_skill,
Фаза 1: «Пошук відділень на checkout — лише з локальної БД», без live-запиту)."""
from django.db import connection
from django.db.models import Case, IntegerField, Value, When
from django.db.models.expressions import RawSQL
from django.db.models.functions import Length, Lower

from src.shipping.models import NPCity, NPWarehouse

# ctype=C на Postgres: звичайний LOWER/ILIKE не згортає кирилицю («киї» ≠ «Киї»).
_LOWER_UTF8_PG = 'LOWER((%s)::text COLLATE "C.UTF-8")'


def _lower_ci(field: str):
    """Case-insensitive lower для кирилиці (Postgres ctype=C + SQLite у тестах)."""
    if connection.vendor == "postgresql":
        return RawSQL(_LOWER_UTF8_PG % field, [])
    return Lower(field)


def search_cities(query: str):
    """Усі активні збіги без [:N]. Порожній запит — без підказок.

    Ранжування: точна назва → назва починається з запиту → містить у середині.
    Інакше «киї» віддає села «… (Київська обл.)» раніше за «Київ» (алфавіт + старий limit).
    """
    qs = NPCity.objects.filter(is_active=True)
    needle = (query or "").casefold().strip()
    if not needle:
        return qs.none()

    qs = qs.annotate(name_lower=_lower_ci("name")).filter(name_lower__contains=needle).annotate(
        _rank=Case(
            When(name_lower=needle, then=Value(0)),
            When(name_lower__startswith=needle, then=Value(1)),
            default=Value(2),
            output_field=IntegerField(),
        ),
    )
    return qs.order_by("_rank", Length("name"), "name")


def search_warehouses(city_id: int, query: str = ""):
    """Відділення і поштомати для checkout; вантажні термінали (Cargo) не показуємо.

    Без limit — усі точки міста (UI вже зі скролом у .suggestions-list).
    """
    qs = NPWarehouse.objects.filter(is_active=True, city_id=city_id).exclude(
        category__iexact=NPWarehouse.CATEGORY_CARGO,
    )
    needle = (query or "").casefold().strip()
    if needle:
        qs = qs.annotate(desc_lower=_lower_ci("description")).filter(desc_lower__contains=needle)
    return qs.annotate(
        _kind=Case(
            When(category__iexact=NPWarehouse.CATEGORY_POSTOMAT, then=Value(1)),
            default=Value(0),
            output_field=IntegerField(),
        ),
    ).order_by("_kind", "number", "description")


def is_reference_data_available() -> bool:
    """Чи вже синкнуто довідник міст. Якщо немає — checkout падає на текстові поля
    (Фаза 0.5: не прикидатися live)."""
    return NPCity.objects.exists()
