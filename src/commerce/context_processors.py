"""Кількість товарів у кошику — для бейджа в шапці на КОЖНІЙ сторінці сайту."""
from src.commerce import selectors


def cart_badge(request):
    cart = selectors.get_cart(request)
    count = sum(line.qty for line in selectors.cart_lines(cart)) if cart else 0
    return {"cart_items_count": count}
