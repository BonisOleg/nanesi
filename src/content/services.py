"""Підписка на email (popup/інлайн, лист Nanesi п.10) — видача одноразового промокоду.

Повторна підписка з тим самим email НЕ створює другий промокод (idempotent) —
повертається вже виданий раніше код, щоб не роздавати знижку безлімітно на один email.
"""
import random
import string

from django.db import transaction

from src.commerce.models import PromoCode
from src.content.models import NewsletterLead, SiteSettings

_CODE_ALPHABET = string.ascii_uppercase + string.digits


def _generate_unique_code(prefix: str = "WELCOME") -> str:
    for _attempt in range(20):
        candidate = f"{prefix}-{''.join(random.choices(_CODE_ALPHABET, k=6))}"
        if not PromoCode.objects.filter(code=candidate).exists():
            return candidate
    raise RuntimeError("Не вдалося згенерувати унікальний промокод")


@transaction.atomic
def subscribe_email(email: str, source: str = NewsletterLead.Source.POPUP) -> NewsletterLead:
    email = email.strip().lower()
    existing = NewsletterLead.objects.select_related("promo_code").filter(email=email).first()
    if existing is not None:
        return existing

    settings_ = SiteSettings.load()
    promo_code = PromoCode.objects.create(
        code=_generate_unique_code(),
        discount_type=PromoCode.DiscountType.PERCENT,
        discount_value=settings_.promo_popup_discount_percent or 10,
        max_uses=1,
        is_active=True,
    )
    return NewsletterLead.objects.create(email=email, source=source, promo_code=promo_code)
