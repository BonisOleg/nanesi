"""Тільки читання (ecommerce_business_logic_skill, шар selectors) — публічний каталог.
Рейтинг/кількість відгуків рахуються тут агрегатами, щоб не робити N+1 у шаблонах."""
from decimal import Decimal
from urllib.parse import urlencode

from django.db.models import Avg, Count, Min, Prefetch, Q, QuerySet
from django.utils.text import slugify
from django.utils.translation import get_language, gettext_lazy as _

from src.catalog.models import (
    Attribute,
    AttributeValue,
    Brand,
    Category,
    Collection,
    Product,
    ProductVariant,
)

# Whitelist GET-ключів фасетів (= Attribute.code). Нова група → додати сюди + seed.
ATTRIBUTE_FILTER_KEYS = (
    "skin_type",
    "concern",
    "country",
    "ingredient",
    "age",
    "spf",
)


def pdp_attribute_groups(product: Product) -> list[dict]:
    """Характеристики для картки: групи з show_on_pdp, umbrella ховає siblings."""
    grouped: dict[int, dict] = {}
    for pav in product.product_attribute_values.all():
        value = pav.attribute_value
        attr = value.attribute
        if not attr.show_on_pdp:
            continue
        bucket = grouped.get(attr.pk)
        if bucket is None:
            bucket = {
                "name": attr.name,
                "sort_order": attr.sort_order,
                "values": [],
            }
            grouped[attr.pk] = bucket
        bucket["values"].append(value)

    result: list[dict] = []
    for bucket in sorted(grouped.values(), key=lambda item: (item["sort_order"], item["name"])):
        values = sorted(bucket["values"], key=lambda item: (item.sort_order, item.pk))
        umbrellas = [item for item in values if item.is_umbrella]
        result.append({
            "name": bucket["name"],
            "values": umbrellas or values,
        })
    return result


def _with_rating(qs: QuerySet[Product]) -> QuerySet[Product]:
    approved = Q(reviews__is_approved=True)
    return qs.annotate(
        rating_avg=Avg("reviews__rating", filter=approved),
        reviews_count=Count("reviews", filter=approved, distinct=True),
        min_price=Min("variants__retail_price", filter=Q(variants__is_active=True)),
    )


def visible_products() -> QuerySet[Product]:
    return _with_rating(
        Product.objects.filter(is_active=True).select_related("brand", "category").prefetch_related(
            "images", "variants",
        )
    )


def top_level_categories() -> QuerySet[Category]:
    return Category.objects.filter(is_active=True, parent__isnull=True).order_by("sort_order", "name")


def header_nav_categories() -> QuerySet[Category]:
    """Корені для нижньої смуги шапки — лише з прапорцем show_in_header."""
    return top_level_categories().filter(show_in_header=True)


def nav_category_tree() -> QuerySet[Category]:
    """Повне дерево коренів — кнопка «Каталог» і мобільна панель."""
    children = Category.objects.filter(is_active=True).order_by("sort_order", "name")
    return top_level_categories().prefetch_related(Prefetch("children", queryset=children))


def volume_slug(volume: str) -> str:
    return slugify((volume or "").strip(), allow_unicode=True)


def localize_volume_label(label: str, lang: str | None = None) -> str:
    """Вітринні одиниці об'єму: uk «мл/г/рефіл» → en «ml/g/refill», ru «рефил».

    Значення в БД лишаються українськими; slug фільтра — від канону uk.
    """
    import re

    text = (label or "").strip()
    if not text:
        return text
    code = (lang or get_language() or "uk").split("-")[0].lower()
    if code == "uk":
        return text
    if code == "ru":
        return text.replace("рефіл", "рефил")
    if code == "en":
        text = text.replace("рефіл", "refill")
        text = re.sub(r"(?<=\d)\s*мл\b", " ml", text)
        text = re.sub(r"(?<=\d)\s*г\b", " g", text)
        return text
    return text


def active_brands() -> QuerySet[Brand]:
    return Brand.objects.filter(is_active=True).order_by("name")


SORT_OPTIONS = [
    ("popular", _("За популярністю")),
    ("price-asc", _("Ціна: зростання")),
    ("price-desc", _("Ціна: спадання")),
    ("name", _("За назвою")),
]


def apply_sort(qs: QuerySet[Product], sort: str) -> QuerySet[Product]:
    if sort == "price-asc":
        return qs.order_by("min_price", "pk")
    if sort == "price-desc":
        return qs.order_by("-min_price", "pk")
    if sort == "name":
        return qs.order_by("name")
    return qs.order_by("-rating_avg", "-reviews_count", "-created_at")


def parse_catalog_filters(request) -> dict:
    """GET → dict фільтрів. Атрибути лише з ATTRIBUTE_FILTER_KEYS; об'єм — зі Variant."""
    attr_filters = {
        key: request.GET.getlist(key)
        for key in ATTRIBUTE_FILTER_KEYS
        if request.GET.getlist(key)
    }
    return {
        "brand_slugs": request.GET.getlist("brand"),
        "category_slugs": request.GET.getlist("category"),
        "attr_filters": attr_filters,
        "volume_slugs": [v for v in request.GET.getlist("volume") if v],
        "stock_only": ("stock" in request.GET) if request.GET else True,
        "sale_only": request.GET.get("sale") == "1",
        "query": request.GET.get("q", "").strip(),
        "price_min": _parse_filter_decimal(request.GET.get("price_min", "")),
        "price_max": _parse_filter_decimal(request.GET.get("price_max", "")),
    }


def _parse_filter_decimal(raw: str) -> Decimal | None:
    from decimal import InvalidOperation

    raw = (raw or "").strip().replace(",", ".")
    if not raw:
        return None
    try:
        value = Decimal(raw)
    except InvalidOperation:
        return None
    return value if value >= 0 else None


def filters_reset_url(request_path: str, query: str) -> str:
    if query:
        return f"{request_path}?{urlencode({'q': query})}"
    return request_path


def filter_groups_for_catalog() -> list[dict]:
    """Групи з значеннями, призначеними хоча б одному активному товару."""
    used_ids = (
        AttributeValue.objects.filter(products__is_active=True)
        .values_list("id", flat=True)
        .distinct()
    )
    groups = (
        Attribute.objects.filter(is_filterable=True, code__in=ATTRIBUTE_FILTER_KEYS)
        .prefetch_related(
            Prefetch(
                "values",
                queryset=AttributeValue.objects.filter(id__in=used_ids).order_by("sort_order", "value"),
            )
        )
        .order_by("sort_order", "name")
    )
    result = []
    for attr in groups:
        values = list(attr.values.all())
        if values:
            result.append({"attribute": attr, "values": values})
    return result


def volume_options_for_catalog() -> list[dict]:
    """Унікальні об'єми з активних варіантів → {slug, label} для сайдбара."""
    raw = (
        ProductVariant.objects.filter(is_active=True, product__is_active=True)
        .exclude(volume="")
        .values_list("volume", flat=True)
        .distinct()
    )
    options = []
    seen: set[str] = set()
    for label in raw:
        slug = volume_slug(label)
        if not slug or slug in seen:
            continue
        seen.add(slug)
        options.append({"slug": slug, "label": localize_volume_label(label)})
    return sorted(options, key=lambda item: item["label"])


def _volumes_matching_slugs(volume_slugs: list[str]) -> list[str]:
    wanted = set(volume_slugs)
    labels = (
        ProductVariant.objects.filter(is_active=True, product__is_active=True)
        .exclude(volume="")
        .values_list("volume", flat=True)
        .distinct()
    )
    return [label for label in labels if volume_slug(label) in wanted]


def category_ids_with_descendants(slugs: list[str] | None = None, *, category: Category | None = None) -> list[int]:
    """ID категорії + прямих дітей (як на сторінці категорії). Для чекбокс-фільтра теж."""
    ids: set[int] = set()
    cats: list[Category] = []
    if category is not None:
        cats.append(category)
    if slugs:
        cats.extend(list(Category.objects.filter(slug__in=slugs, is_active=True)))
    for cat in cats:
        ids.add(cat.pk)
        ids.update(cat.children.filter(is_active=True).values_list("pk", flat=True))
    return list(ids)


def filter_products(
    base_qs: QuerySet[Product],
    *,
    category: Category | None = None,
    brand_slugs: list[str] | None = None,
    category_slugs: list[str] | None = None,
    attr_filters: dict[str, list[str]] | None = None,
    volume_slugs: list[str] | None = None,
    stock_only: bool = False,
    sale_only: bool = False,
    query: str | None = None,
    price_min: Decimal | None = None,
    price_max: Decimal | None = None,
) -> QuerySet[Product]:
    qs = base_qs

    cat_ids = category_ids_with_descendants(category_slugs, category=category)
    if cat_ids:
        qs = qs.filter(
            Q(category_id__in=cat_ids) | Q(additional_categories__id__in=cat_ids)
        ).distinct()

    if brand_slugs:
        qs = qs.filter(brand__slug__in=brand_slugs)

    # OR у групі (slug__in), AND між групами (окремий .filter у циклі)
    if attr_filters:
        for code, value_slugs in attr_filters.items():
            if code not in ATTRIBUTE_FILTER_KEYS or not value_slugs:
                continue
            qs = qs.filter(
                attribute_values__attribute__code=code,
                attribute_values__slug__in=value_slugs,
            ).distinct()

    if volume_slugs:
        matched = _volumes_matching_slugs(volume_slugs)
        if matched:
            qs = qs.filter(variants__is_active=True, variants__volume__in=matched).distinct()
        else:
            qs = qs.none()

    if stock_only:
        qs = qs.filter(variants__is_active=True, variants__stock_quantity__gt=0).distinct()

    if sale_only:
        qs = qs.filter(variants__sale_price__isnull=False).distinct()

    if price_min is not None:
        qs = qs.filter(
            Q(variants__is_active=True)
            & (
                Q(variants__sale_price__gte=price_min)
                | Q(variants__sale_price__isnull=True, variants__retail_price__gte=price_min)
            )
        ).distinct()

    if price_max is not None:
        qs = qs.filter(
            Q(variants__is_active=True)
            & (
                Q(variants__sale_price__lte=price_max)
                | Q(variants__sale_price__isnull=True, variants__retail_price__lte=price_max)
            )
        ).distinct()

    if query:
        qs = qs.filter(
            Q(name__icontains=query) | Q(brand__name__icontains=query) | Q(variants__sku__icontains=query)
        ).distinct()

    return qs


def related_products(product: Product, limit: int = 4) -> QuerySet[Product]:
    qs = visible_products().filter(category=product.category).exclude(pk=product.pk)
    if qs.count() < limit:
        qs = visible_products().exclude(pk=product.pk)
    return qs.order_by("-rating_avg", "-created_at")[:limit]


def bought_together(product: Product, limit: int = 4) -> list[Product]:
    """Товари, що найчастіше трапляються в одних замовленнях із цим (Nanesi п.6).

    Якщо історії замовлень ще немає — фолбек на ту саму категорію / бренд.
    """
    from src.commerce.models import Order, OrderItem

    order_ids = (
        OrderItem.objects.filter(product_variant__product=product)
        .exclude(order__status=Order.Status.CANCELLED)
        .values_list("order_id", flat=True)
        .distinct()
    )
    companion_ids = list(
        OrderItem.objects.filter(order_id__in=order_ids)
        .exclude(product_variant__product=product)
        .values("product_variant__product_id")
        .annotate(freq=Count("id"))
        .order_by("-freq")
        .values_list("product_variant__product_id", flat=True)[:limit]
    )
    if companion_ids:
        products_by_id = {
            p.pk: p for p in visible_products().filter(pk__in=companion_ids)
        }
        return [products_by_id[pk] for pk in companion_ids if pk in products_by_id]

    fallback = list(
        visible_products()
        .filter(Q(category=product.category) | Q(brand=product.brand))
        .exclude(pk=product.pk)
        .order_by("-is_hit", "-rating_avg", "-created_at")[:limit]
    )
    return fallback


def collection_by_slug(slug: str) -> Collection | None:
    return (
        Collection.objects.filter(slug=slug, is_active=True)
        .prefetch_related("products")
        .first()
    )


def products_for_collection(collection: Collection) -> QuerySet[Product]:
    """Підбірка: ручний M2M, або авто за kind (hit/new/sale)."""
    qs = visible_products()
    manual_ids = list(collection.products.values_list("pk", flat=True))
    if manual_ids:
        return qs.filter(pk__in=manual_ids).order_by("-created_at")
    if collection.kind == Collection.Kind.HIT:
        return qs.filter(is_hit=True).order_by("-created_at")
    if collection.kind == Collection.Kind.NEW:
        return qs.filter(is_new=True).order_by("-created_at")
    if collection.kind == Collection.Kind.SALE:
        return qs.filter(variants__sale_price__isnull=False).distinct().order_by("-created_at")
    return qs.none()


def search_suggest(query: str, *, limit: int = 8) -> list[Product]:
    """Підказки для хедера: назва / бренд / SKU (як плейсхолдер пошуку)."""
    q = (query or "").strip()
    if len(q) < 2:
        return []
    return list(
        visible_products()
        .filter(
            Q(name__icontains=q)
            | Q(brand__name__icontains=q)
            | Q(variants__sku__icontains=q)
        )
        .distinct()
        .order_by("name")[:limit]
    )


def home_category_circles() -> QuerySet[Category]:
    """Кола на головній: узгоджені кореневі напрями (8-ме — «Акції» у шаблоні)."""
    return top_level_categories()[:7]


_HOME_COLLECTION_SLUGS = ("novynky", "hity", "aktsii")


def home_collection_product_sections(*, limit: int = 8) -> list[dict]:
    """Окремі сітки на головній: Новинки → Хіти → Акції (за slug seed)."""
    sections: list[dict] = []
    for slug in _HOME_COLLECTION_SLUGS:
        collection = (
            Collection.objects.filter(slug=slug, is_active=True)
            .prefetch_related("products")
            .first()
        )
        if collection is None:
            continue
        products = list(products_for_collection(collection)[:limit])
        if not products:
            continue
        sections.append({"collection": collection, "products": products})
    return sections


def home_sections() -> dict:
    return {
        "categories": home_category_circles(),
        # Макет: 4 промо-картки (хіти/новинки/акції + кастомна)
        "promo_collections": Collection.objects.filter(is_active=True).order_by("sort_order", "name")[:4],
        "collection_product_sections": home_collection_product_sections(),
    }
