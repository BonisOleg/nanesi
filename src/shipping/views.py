"""AJAX-пошук для checkout: місто/відділення НП — лише з локальної БД (Фаза 1).

Якщо довідник ще не синкнуто (немає NP_API_KEY) — `configured: false`, фронт
показує звичайні текстові поля замість автодоповнення (Фаза 0.5, не прикидатися live).
"""
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from src.shipping.models import NPCity
from src.shipping.selectors import is_reference_data_available, search_cities, search_warehouses
from src.shipping.services import ShippingConfigError, ensure_warehouses_synced


@require_GET
def np_cities(request):
    query = request.GET.get("q", "").strip()
    configured = is_reference_data_available()
    cities = search_cities(query) if configured else []
    return JsonResponse({
        "configured": configured,
        "results": [{"id": c.pk, "ref": c.ref, "name": str(c)} for c in cities],
    })


@require_GET
def np_warehouses(request):
    city_id = request.GET.get("city")
    query = request.GET.get("q", "").strip()
    if not city_id:
        return JsonResponse({"configured": False, "results": []})

    city = NPCity.objects.filter(pk=city_id).first()
    if city is None:
        return JsonResponse({"configured": False, "results": []})

    try:
        ensure_warehouses_synced(city)
        configured = True
    except ShippingConfigError:
        configured = False

    warehouses = search_warehouses(city.pk, query) if configured else []
    return JsonResponse({
        "configured": configured,
        "results": [
            {"id": w.pk, "ref": w.ref, "name": w.display_name(), "kind": w.kind}
            for w in warehouses
        ],
    })
