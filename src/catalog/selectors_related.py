"""Ручні/авто блоки «Схожі товари» та «З цим купують»."""
from django.db.models import Count, OuterRef, Q, Subquery

from src.catalog.models import Product, ProductCrossSell, ProductSimilar
from src.catalog.selectors import visible_products


def _auto_related_products(product: Product, limit: int = 4) -> list[Product]:
    qs = visible_products().filter(category=product.category).exclude(pk=product.pk)
    if qs.count() < limit:
        qs = visible_products().exclude(pk=product.pk)
    return list(qs.order_by("-rating_avg", "-created_at")[:limit])


def _manual_related_products(product: Product, limit: int) -> list[Product]:
    """Ручні схожі товари вітрини. Порожній список — фолбек на автодобір."""
    capped = min(limit, 8)
    if capped <= 0:
        return []
    link = ProductSimilar.objects.filter(
        from_product_id=product.pk,
        to_product_id=OuterRef("pk"),
    )
    return list(
        visible_products()
        .filter(
            pk__in=ProductSimilar.objects.filter(from_product_id=product.pk)
            .exclude(to_product_id=product.pk)
            .values("to_product_id"),
        )
        .annotate(
            _sim_position=Subquery(link.values("position")[:1]),
            _sim_row=Subquery(link.values("pk")[:1]),
        )
        .order_by("_sim_position", "_sim_row")[:capped]
    )


def related_products(
    product: Product, limit: int = 4, manual_limit: int = 8,
) -> list[Product]:
    """Товари блоку «Схожі товари».

    Ручні зв'язки — до manual_limit (типово 8). Якщо після фільтра вітрини
    лишився хоч один товар — лише вони. Інакше авто: категорія, інакше
    увесь каталог за рейтингом (не більше limit).
    """
    manual = _manual_related_products(product, manual_limit)
    if manual:
        return manual
    return _auto_related_products(product, limit)


def _manual_bought_together(product: Product, limit: int) -> list[Product]:
    """Ручні супутні товари вітрини. Порожній список — фолбек на автодобір."""
    capped = min(limit, 8)
    if capped <= 0:
        return []
    link = ProductCrossSell.objects.filter(
        from_product_id=product.pk,
        to_product_id=OuterRef("pk"),
    )
    return list(
        visible_products()
        .filter(
            pk__in=ProductCrossSell.objects.filter(from_product_id=product.pk)
            .exclude(to_product_id=product.pk)
            .values("to_product_id"),
        )
        .annotate(
            _cs_position=Subquery(link.values("position")[:1]),
            _cs_row=Subquery(link.values("pk")[:1]),
        )
        .order_by("_cs_position", "_cs_row")[:capped]
    )


def bought_together(
    product: Product, limit: int = 4, manual_limit: int = 8,
) -> list[Product]:
    """Товари блоку «З цим купують».

    Ручні зв'язки — до manual_limit (типово 8). Якщо після фільтра вітрини
    лишився хоч один товар — лише вони (position, потім id рядка), без
    домішування авто. Інакше сусіди в замовленнях або фолбек на категорію /
    бренд, не більше limit (типово 4).
    """
    manual = _manual_bought_together(product, manual_limit)
    if manual:
        return manual

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
