"""Тільки читання — пошук міст/відділень ЛИШЕ з локальної БД (novaposhta_skill,
Фаза 1: «Пошук відділень на checkout — лише з локальної БД», без live-запиту)."""
from functools import lru_cache

from django.db import connection
from django.db.models import Case, CharField, Func, IntegerField, Q, Value, When
from django.db.models.expressions import RawSQL
from django.db.models.functions import Length, Lower

from src.shipping.models import NPCity, NPWarehouse
from src.shipping.utils import APOSTROPHE_TO_ASCII, latin_city_needle

# Checkout suggestions: без ліміту Київ віддає тисячі DOM-вузлів і «вбиває» мобільний Safari.
SUGGESTIONS_LIMIT = 40
# Міста на checkout: стеля 40, щоб відповідь лишалась ~40 КБ (P2). limit=None — без зрізу.
CITY_SUGGESTIONS_LIMIT = 40

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


def _sqlite_np_lower(value):
    """Unicode-lower: вбудований SQLite LOWER() згортає лише ASCII."""
    if value is None:
        return None
    return str(value).lower()


def register_sqlite_np_lower(sender, connection, **kwargs):
    """NP_LOWER на кожному новому SQLite-з'єднанні (тести і локальний sqlite)."""
    if connection.vendor != "sqlite" or connection.connection is None:
        return
    connection.connection.create_function(
        "NP_LOWER", 1, _sqlite_np_lower, deterministic=True,
    )


def normalize_query(q: str) -> str:
    """strip + casefold + єдиний ASCII-апостроф для пошуку по довіднику НП."""
    return (q or "").strip().casefold().translate(APOSTROPHE_TO_ASCII)


def _is_latin_city_query(query: str) -> bool:
    """Латиниця без кирилиці — шукаємо name_latin, інакше лишаємо кириличний шлях."""
    has_latin = False
    for ch in query or "":
        if "A" <= ch <= "Z" or "a" <= ch <= "z":
            has_latin = True
        elif "\u0400" <= ch <= "\u04FF":
            return False
    return has_latin


def _lower_ci(field: str):
    """Case-insensitive lower для кирилиці (Postgres ctype=C + SQLite у тестах)."""
    if connection.vendor == "postgresql":
        coll = _pg_cyrillic_lower_collation()
        if coll:
            return RawSQL(f'LOWER(({field})::text COLLATE "{coll}")', [])
        return Lower(field)
    if connection.vendor == "sqlite":
        return Func(field, function="NP_LOWER", output_field=CharField())
    return Lower(field)


def search_cities(query: str, *, limit: int | None = CITY_SUGGESTIONS_LIMIT):
    """Активні збіги. Порожній запит — без підказок.

    Ранжування: точна назва → назва починається з запиту → містить у середині,
    далі коротша назва. Інакше «киї» віддає села «… (Київська обл.)» раніше за «Київ».
    Латиниця без кирилиці шукається по name_latin (КМУ 2010 + екзоніми).
    UI ріжеться до CITY_SUGGESTIONS_LIMIT; limit=None — повний список.
    """
    qs = NPCity.objects.filter(is_active=True)
    if _is_latin_city_query(query):
        needle = latin_city_needle(query)
        field = "name_latin"
    else:
        needle = normalize_query(query)
        field = "name"
    if not needle:
        return qs.none()

    qs = qs.annotate(name_lower=_lower_ci(field)).filter(name_lower__contains=needle).annotate(
        _rank=Case(
            When(name_lower=needle, then=Value(0)),
            When(name_lower__startswith=needle, then=Value(1)),
            default=Value(2),
            output_field=IntegerField(),
        ),
    ).order_by("_rank", Length("name"), "name")
    if limit is not None and limit >= 0:
        return qs[:limit]
    return qs


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
        needle = normalize_query(needle)
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
