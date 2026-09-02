"""Кількість і id товарів у кошику — для бейджа й стану «в кошику» на вітрині."""
from src.commerce import selectors


def cart_badge(request):
    cart = selectors.get_cart(request)
    lines = selectors.cart_lines(cart) if cart else []
    return {
        "cart_items_count": sum(line.qty for line in lines),
        "cart_product_ids": {line.product_id for line in lines},
        "cart_variant_ids": {line.variant_id for line in lines},
    }
