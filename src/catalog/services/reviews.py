"""Створення відгуку з фото (Підетап 3, Відповіді п.8).

«Підтверджена покупка» виставляється автоматично, якщо у користувача є
не скасоване замовлення з цим товаром.
"""
import bleach
from django.db import transaction

from src.catalog.models import Product, Review, ReviewImage
from src.core.utils.images import validate_image

_ALLOWED_TAGS: list[str] = []  # відгук — лише текст, без HTML


def has_verified_purchase(user, product: Product) -> bool:
    if not user or not user.is_authenticated:
        return False
    from src.commerce.models import Order

    return (
        Order.objects.filter(user=user, items__product_variant__product=product)
        .exclude(status=Order.Status.CANCELLED)
        .exists()
    )


@transaction.atomic
def create_review(*, product: Product, user, author_name: str, rating: int, text: str, photos: list) -> Review:
    review = Review.objects.create(
        product=product,
        user=user if user and user.is_authenticated else None,
        author_name="" if user and user.is_authenticated else author_name,
        rating=rating,
        text=bleach.clean(text or "", tags=_ALLOWED_TAGS, strip=True),
        is_verified_purchase=has_verified_purchase(user, product),
        is_approved=False,
    )
    for i, photo in enumerate(photos):
        validate_image(photo)
        ReviewImage.objects.create(review=review, image=photo, sort_order=i)
    return review
