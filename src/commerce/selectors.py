"""Тільки читання (ecommerce_business_logic_skill, шар selectors). Ціна — завжди
жива з ProductVariant, ніколи з кешу кошика (SEC-02/06)."""
from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal

from src.commerce.models import Cart, Order
from src.content.models import SiteSettings

_VOLUME_TOKEN_RE = re.compile(
    r"(?P<num>\d+(?:[.,]\d+)?)\s*(?P<unit>ml|мл|g|г)\b",
    re.IGNORECASE,
)
_UNIT_ALIASES = {
    "ml": ("ml", "мл"),
    "мл": ("ml", "мл"),
    "g": ("g", "г"),
    "г": ("g", "г"),
}


def _volume_already_in_name(name: str, volume: str) -> bool:
    """True, якщо об'єм уже в назві (напр. «… 60 ml» + поле «60 мл»)."""
    vol = (volume or "").strip()
    if not vol or not name:
        return False
    match = _VOLUME_TOKEN_RE.search(vol)
    if not match:
        return vol.lower() in name.lower()
    num = match.group("num")
    unit = match.group("unit").lower()
    name_l = name.lower()
    for alias in _UNIT_ALIASES.get(unit, (unit,)):
        if re.search(rf"{re.escape(num)}\s*{re.escape(alias)}\b", name_l):
            return True
    return False


def get_cart(request) -> Cart | None:
    """Лише пошук — без створення (створення це мутація, services.get_or_create_cart)."""
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user, status=Cart.Status.OPEN).first()
        if cart:
            return cart
    session_key = request.session.session_key
    if not session_key:
        return None
    return Cart.objects.filter(session_key=session_key, status=Cart.Status.OPEN).first()


@dataclass
class CartLine:
    item_id: int
    variant_id: int
    product_id: int
    name: str
    url: str
    sku: str
    shade: str
    volume: str
    unit_price: Decimal
    qty: int
    line_total: Decimal
    in_stock: bool
    stock_quantity: int

    @property
    def variant_label(self) -> str:
        """Підпис під назвою: без дубля об'єму, якщо він уже в назві товару."""
        parts: list[str] = []
        if self.shade:
            parts.append(self.shade)
        if self.volume and not _volume_already_in_name(self.name, self.volume):
            parts.append(self.volume)
        return " / ".join(parts)


def cart_lines(cart: Cart | None) -> list[CartLine]:
    if cart is None:
        return []
    lines = []
    items = cart.items.select_related("product_variant", "product_variant__product").order_by("added_at")
    for item in items:
        variant = item.product_variant
        product = variant.product
        unit_price = variant.current_price
        lines.append(CartLine(
            item_id=item.pk,
            variant_id=variant.pk,
            product_id=product.pk,
            name=product.name,
            url=f"{product.get_absolute_url()}?variant={variant.pk}",
            sku=variant.sku,
            shade=variant.shade,
            volume=variant.volume,
            unit_price=unit_price,
            qty=item.qty,
            line_total=unit_price * item.qty,
            in_stock=variant.in_stock,
            stock_quantity=variant.stock_quantity,
        ))
    return lines


def cart_subtotal(lines: list[CartLine]) -> Decimal:
    return sum((line.line_total for line in lines), Decimal("0"))


def format_uah_amount(value: Decimal) -> str:
    """Цілі — «300»; дробові — «300,50»."""
    quantized = (value or Decimal("0")).quantize(Decimal("0.01"))
    if quantized == quantized.to_integral_value():
        return str(int(quantized))
    return f"{quantized:.2f}".replace(".", ",")


@dataclass
class FreeShippingProgress:
    threshold: Decimal | None
    remaining: Decimal
    reached: bool
    percent: int
    remaining_display: str


def free_shipping_progress(amount: Decimal) -> FreeShippingProgress:
    """Прогрес до порогу з SiteSettings.free_shipping_threshold.

    amount — сума товарів ДО промокоду (знижка не відкочує безкоштовну доставку).
    """
    threshold = SiteSettings.load().free_shipping_threshold
    empty = FreeShippingProgress(
        threshold=None, remaining=Decimal("0"), reached=False,
        percent=0, remaining_display="0",
    )
    if not threshold or threshold <= 0:
        return empty
    remaining = max(Decimal("0"), threshold - amount)
    reached = amount >= threshold
    if reached:
        percent = 100
    else:
        percent = int((amount / threshold * 100).quantize(Decimal("1")))
        percent = min(99, max(0, percent))
    return FreeShippingProgress(
        threshold=threshold,
        remaining=remaining,
        reached=reached,
        percent=percent,
        remaining_display=format_uah_amount(remaining),
    )


def available_delivery_methods() -> list[tuple[str, str]]:
    settings_obj = SiteSettings.load()
    methods = []
    if settings_obj.nova_poshta_enabled:
        methods.append((Order.DeliveryMethod.NOVA_POSHTA_WAREHOUSE, Order.DeliveryMethod.NOVA_POSHTA_WAREHOUSE.label))
    if settings_obj.ukrposhta_enabled:
        methods.append((Order.DeliveryMethod.UKRPOSHTA, Order.DeliveryMethod.UKRPOSHTA.label))
    return methods


def available_payment_methods() -> list[tuple[str, str]]:
    from django.conf import settings as dj_settings

    settings_obj = SiteSettings.load()
    methods = []
    if settings_obj.card_payment_enabled and dj_settings.LIQPAY_PUBLIC_KEY:
        methods.append((Order.PaymentMethod.CARD_ONLINE, Order.PaymentMethod.CARD_ONLINE.label))
    if settings_obj.cash_on_delivery_enabled:
        methods.append((Order.PaymentMethod.CASH_ON_DELIVERY, Order.PaymentMethod.CASH_ON_DELIVERY.label))
    if settings_obj.bank_transfer_enabled:
        methods.append((Order.PaymentMethod.BANK_TRANSFER, Order.PaymentMethod.BANK_TRANSFER.label))
    return methods


def alternate_payment_methods_after_card() -> list[tuple[str, str]]:
    """Способи оплати для перемикання після помилки картки (без card_online)."""
    return [
        (code, label)
        for code, label in available_payment_methods()
        if code != Order.PaymentMethod.CARD_ONLINE
    ]


def my_orders(user):
    """SEC-01: замовлення лише власника."""
    return Order.objects.filter(user=user).order_by("-created_at")


def get_order_for_thanks(request, order_number: str) -> Order | None:
    """Гість-thanks: доступ лише якщо номер збігається з session['last_order_number']
    (SEC-01, гостьовий варіант) — не голий pk із query-параметра."""
    last_number = request.session.get("last_order_number")
    if last_number and last_number == order_number:
        return Order.objects.filter(number=order_number).first()
    if request.user.is_authenticated:
        return Order.objects.filter(number=order_number, user=request.user).first()
    return None
