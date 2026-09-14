"""Тільки читання — пошук міст/відділень ЛИШЕ з локальної БД (novaposhta_skill,
Фаза 1: «Пошук відділень на checkout — лише з локальної БД», без live-запиту)."""
from functools import lru_cache

from django.db import connection
from django.db.models import Case, IntegerField, Q, Value, When
from django.db.models.expressions import RawSQL
from django.db.models.functions import Length, Lower

from src.shipping.models import NPCity, NPWarehouse

# Checkout suggestions: без ліміту Київ віддає тисячі DOM-вузлів і «вбиває» мобільний Safari.
SUGGESTIONS_LIMIT = 40

# ctype=C: звичайний LOWER/ILIKE не згортає кирилицю («киї» ≠ «Киї»).
# Alpine Postgres має ICU (und-x-icu), glibc-образи — часто C.UTF-8; hardcode одного ламає інший.
_PG_LOWER_COLLATIONS = ("und-x-icu", "uk-x-icu", "C.UTF-8")


@lru_cache(maxsize=1)
def _pg_cyrillic_lower_collation() -> str | None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT collname
            FROM pg_collation
            WHERE collname = ANY(%s)
            ORDER BY array_position(%s::text[], collname)
            LIMIT 1
            """,
            [list(_PG_LOWER_COLLATIONS), list(_PG_LOWER_COLLATIONS)],
        )
        row = cursor.fetchone()
    return row[0] if row else None


def _lower_ci(field: str):
    """Case-insensitive lower для кирилиці (Postgres ctype=C + SQLite у тестах)."""
    if connection.vendor == "postgresql":
        coll = _pg_cyrillic_lower_collation()
        if coll:
            return RawSQL(f'LOWER(({field})::text COLLATE "{coll}")', [])
        return Lower(field)
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


def search_warehouses(city_id: int, query: str = "", *, limit: int = SUGGESTIONS_LIMIT):
    """Відділення і поштомати для checkout; вантажні термінали (Cargo) не показуємо.

    Ліміт обовʼязковий для UI. Цифровий запит («12», «№12») — спочатку точний number.
    """
    qs = NPWarehouse.objects.filter(is_active=True, city_id=city_id).exclude(
        category__iexact=NPWarehouse.CATEGORY_CARGO,
    ).annotate(
        _kind=Case(
            When(category__iexact=NPWarehouse.CATEGORY_POSTOMAT, then=Value(1)),
            default=Value(0),
            output_field=IntegerField(),
        ),
    )

    needle = (query or "").strip().lstrip("№#").casefold().strip()
    if needle.isdigit():
        qs = qs.filter(
            Q(number=needle) | Q(number__startswith=needle) | Q(description__icontains=needle),
        ).annotate(
            _rank=Case(
                When(number=needle, then=Value(0)),
                When(number__startswith=needle, then=Value(1)),
                default=Value(2),
                output_field=IntegerField(),
            ),
        ).order_by("_rank", "_kind", "number", "description")
    elif needle:
        qs = qs.annotate(desc_lower=_lower_ci("description")).filter(
            desc_lower__contains=needle,
        ).order_by("_kind", "number", "description")
    else:
        qs = qs.order_by("_kind", "number", "description")

    if limit is not None and limit >= 0:
        return qs[:limit]
    return qs


def is_reference_data_available() -> bool:
    """Чи вже синкнуто довідник міст. Якщо немає — checkout падає на текстові поля
    (Фаза 0.5: не прикидатися live)."""
    return NPCity.objects.exists()
