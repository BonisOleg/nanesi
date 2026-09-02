"""Категорії для навігації + обране (для авторизованих) — на кожній сторінці.
Гість тримає обране в localStorage (Підетап 1), тому тут лише авторизовані."""
from src.catalog import selectors


def nav_context(request):
    wishlist_count = 0
    wishlist_ids: set[int] = set()
    if request.user.is_authenticated:
        wishlist_ids = set(request.user.wishlist_items.values_list("product_id", flat=True))
        wishlist_count = len(wishlist_ids)
    return {
        "nav_categories": list(selectors.nav_category_tree()),
        "header_nav_categories": list(selectors.header_nav_categories()),
        "wishlist_count": wishlist_count,
        "wishlist_ids": wishlist_ids,
    }
