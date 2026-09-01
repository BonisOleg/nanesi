"""Мутації кабінету: синк обраного гостя, тумблер обраного, «Повторити замовлення»."""
from django.db import transaction

from src.accounts.models import User, Wishlist
from src.catalog.models import Product
from src.commerce import services as commerce_services
from src.commerce.models import Order


@transaction.atomic
def sync_guest_wishlist(user: User, product_ids: list[int]) -> None:
    """Гість зайшов в акаунт — локальні id товарів з localStorage додаються до Wishlist
    (без видалення того, що вже було в акаунті — обʼєднання, не заміна)."""
    if not product_ids:
        return
    existing_ids = set(Wishlist.objects.filter(user=user).values_list("product_id", flat=True))
    valid_ids = set(Product.objects.filter(pk__in=product_ids, is_active=True).values_list("pk", flat=True))
    new_ids = valid_ids - existing_ids
    Wishlist.objects.bulk_create([Wishlist(user=user, product_id=pid) for pid in new_ids])


@transaction.atomic
def toggle_wishlist(user: User, product_id: int) -> bool:
    """Повертає True, якщо товар додано, False — якщо видалено."""
    obj, created = Wishlist.objects.get_or_create(user=user, product_id=product_id)
    if not created:
        obj.delete()
        return False
    return True


def repeat_order(request, order: Order) -> tuple[int, list[str]]:
    """Додає позиції замовлення в поточний кошик. Повертає (додано, [назви недоступних])."""
    added = 0
    unavailable: list[str] = []
    for item in order.items.select_related("product_variant"):
        variant = item.product_variant
        if variant is None or not variant.is_active or not variant.in_stock:
            unavailable.append(item.product_name)
            continue
        try:
            commerce_services.add_item(request, variant.pk, qty=item.qty)
            added += 1
        except commerce_services.CartError:
            unavailable.append(item.product_name)
    return added, unavailable
