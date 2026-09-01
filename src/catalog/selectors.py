"""Тільки читання (ecommerce_business_logic_skill, шар selectors) — публічний каталог.
Рейтинг/кількість відгуків рахуються тут агрегатами, щоб не робити N+1 у шаблонах."""
from django.db.models import Avg, Count, Min, Q, QuerySet
from django.utils.translation import gettext_lazy as _

from src.catalog.models import (
    Attribute,
    Brand,
    Category,
    Product,
)


def _with_rating(qs: QuerySet[Product]) -> QuerySet[Product]:
    approved = Q(reviews__is_approved=True)
    return qs.annotate(
        rating_avg=Avg("reviews__rating", filter=approved),
        reviews_count=Count("reviews", filter=approved, distinct=True),
        min_price=Min("variants__retail_price", filter=Q(variants__is_active=True)),
    )


def visible_products() -> QuerySet[Product]:
    return _with_rating(
        Product.objects.filter(is_active=True).select_related("brand", "category").prefetch_related("images")
    )


def top_level_categories() -> QuerySet[Category]:
    return Category.objects.filter(is_active=True, parent__isnull=True).order_by("sort_order", "name")


def filterable_attributes() -> QuerySet[Attribute]:
    return Attribute.objects.filter(is_filterable=True).prefetch_related("values")


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


def filter_products(
    base_qs: QuerySet[Product],
    *,
    category: Category | None = None,
    brand_slugs: list[str] | None = None,
    category_slugs: list[str] | None = None,
    attribute_value_ids: list[int] | None = None,
    stock_only: bool = False,
    sale_only: bool = False,
    query: str | None = None,
) -> QuerySet[Product]:
    qs = base_qs

    if category is not None:
        descendant_ids = [category.pk] + list(category.children.values_list("pk", flat=True))
        qs = qs.filter(
            Q(category_id__in=descendant_ids) | Q(additional_categories__id__in=descendant_ids)
        ).distinct()

    if category_slugs:
        qs = qs.filter(
            Q(category__slug__in=category_slugs) | Q(additional_categories__slug__in=category_slugs)
        ).distinct()

    if brand_slugs:
        qs = qs.filter(brand__slug__in=brand_slugs)

    if attribute_value_ids:
        qs = qs.filter(attribute_values__id__in=attribute_value_ids).distinct()

    if stock_only:
        qs = qs.filter(variants__is_active=True, variants__stock_quantity__gt=0).distinct()

    if sale_only:
        qs = qs.filter(variants__sale_price__isnull=False).distinct()

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


def home_sections() -> dict:
    hits_and_new = visible_products().filter(Q(is_hit=True) | Q(is_new=True)).order_by("-created_at")[:8]
    return {
        "categories": top_level_categories()[:8],
        "hits_and_new": hits_and_new,
    }
