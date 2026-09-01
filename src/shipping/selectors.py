"""Тільки читання — пошук міст/відділень ЛИШЕ з локальної БД (novaposhta_skill,
Фаза 1: «Пошук відділень на checkout — лише з локальної БД», без live-запиту)."""
from src.shipping.models import NPCity, NPWarehouse


def search_cities(query: str, limit: int = 20):
    qs = NPCity.objects.filter(is_active=True)
    if query:
        qs = qs.filter(name__icontains=query)
    return qs.order_by("name")[:limit]


def search_warehouses(city_id: int, query: str = "", limit: int = 50):
    qs = NPWarehouse.objects.filter(is_active=True, city_id=city_id)
    if query:
        qs = qs.filter(description__icontains=query)
    return qs.order_by("number")[:limit]


def is_reference_data_available() -> bool:
    """Чи вже синкнуто довідник міст. Якщо немає — checkout падає на текстові поля
    (Фаза 0.5: не прикидатися live)."""
    return NPCity.objects.exists()
