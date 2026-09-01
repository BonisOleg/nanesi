"""Read-only вибірки для кабінету (ecommerce_business_logic_skill, шар selectors)."""
from django.db.models import QuerySet

from src.accounts.models import User, Wishlist
from src.commerce.models import Order


def user_orders(user: User) -> QuerySet[Order]:
    return Order.objects.filter(user=user).order_by("-created_at")


def user_order_detail(user: User, order_number: str) -> Order | None:
    return (
        Order.objects.filter(user=user, number=order_number)
        .prefetch_related("items", "items__product_variant", "items__product_variant__product")
        .first()
    )


def wishlist_product_ids(user: User) -> set[int]:
    return set(Wishlist.objects.filter(user=user).values_list("product_id", flat=True))


def wishlist_products(user: User):
    from src.catalog.selectors import visible_products

    ids = wishlist_product_ids(user)
    if not ids:
        return visible_products().none()
    return visible_products().filter(pk__in=ids)
