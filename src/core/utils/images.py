"""Конвертація ImageField → WebP (заміна оригіналу) + SEC-05 валідація upload.

Логотипи (SiteSettings.logo, Brand.logo) навмисно поза реєстром.
"""
from __future__ import annotations

import os
from io import BytesIO
from pathlib import Path

from django.apps import apps
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import models
from PIL import Image, ImageOps

WEBP_QUALITY = 85
WEBP_METHOD = 4
MAX_UPLOAD_BYTES = 5 * 1024 * 1024
ALLOWED_IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

# (app_label.ModelName, field_name, max_long_side)
# hero/blog — 1600; картка товару на вітрині ~372px → 800 (2×); решта каталогу — 1200
IMAGE_WEBP_SPECS: list[tuple[str, str, int]] = [
    ("content.SiteSettings", "hero_image", 1600),
    ("content.BlogPost", "cover_image", 1600),
    ("content.HeroBanner", "image", 1280),
    ("content.HeroBanner", "background_image", 1280),
    ("catalog.Category", "image", 1200),
    ("catalog.ProductImage", "image", 800),
    ("catalog.ProductVariant", "shade_image", 1200),
    ("catalog.Collection", "image", 1200),
    ("catalog.ReviewImage", "image", 1200),
]


def validate_image(value) -> None:
    """Extension + розмір + Pillow verify (SEC-05). SVG заборонено."""
    ext = os.path.splitext(value.name)[1].lower()
    if ext not in ALLOWED_IMAGE_EXT:
        raise ValidationError("Дозволені лише JPEG, PNG, WebP або GIF.")
    size = getattr(value, "size", None)
    if size is not None and size > MAX_UPLOAD_BYTES:
        raise ValidationError("Максимум 5 МБ.")
    pos = value.tell() if hasattr(value, "tell") else None
    try:
        img = Image.open(value)
        img.verify()
    except Exception as exc:
        raise ValidationError("Файл не є коректним зображенням.") from exc
    finally:
        if pos is not None and hasattr(value, "seek"):
            value.seek(pos)


def _prepare_image(img: Image.Image) -> Image.Image:
    img = ImageOps.exif_transpose(img)
    if getattr(img, "n_frames", 1) > 1:
        img.seek(0)
    has_alpha = img.mode in ("RGBA", "LA") or (
        img.mode == "P" and "transparency" in img.info
    )
    if has_alpha:
        return img.convert("RGBA")
    return img.convert("RGB")


def image_needs_webp_processing(field_file, max_side: int) -> bool:
    if not field_file or not getattr(field_file, "name", None):
        return False
    is_webp = field_file.name.lower().endswith(".webp")
    try:
        field_file.open("rb")
        with Image.open(field_file) as img:
            img = ImageOps.exif_transpose(img)
            needs_resize = max(img.size) > max_side
        return (not is_webp) or needs_resize
    except Exception:
        return False
    finally:
        try:
            field_file.close()
        except Exception:
            pass


def convert_imagefield_to_webp(
    instance: models.Model,
    field_name: str,
    *,
    max_side: int = 1600,
    quality: int = WEBP_QUALITY,
) -> bool:
    """Замінює файл у полі на WebP (resize по довгій стороні). Повертає True якщо змінено."""
    field_file = getattr(instance, field_name)
    if not field_file or not field_file.name:
        return False

    field_file.open("rb")
    try:
        with Image.open(field_file) as src:
            img = _prepare_image(src.copy())
    finally:
        try:
            field_file.close()
        except Exception:
            pass

    if max(img.size) > max_side:
        img.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)

    buf = BytesIO()
    img.save(buf, format="WEBP", quality=quality, method=WEBP_METHOD)
    buf.seek(0)

    stem = Path(field_file.name).stem
    new_basename = f"{stem}.webp"
    field_file.delete(save=False)
    getattr(instance, field_name).save(
        new_basename,
        ContentFile(buf.getvalue()),
        save=False,
    )
    return True


def get_webp_specs_for_model(model: type[models.Model]) -> list[tuple[str, int]]:
    label = model._meta.label
    return [
        (field_name, max_side)
        for model_label, field_name, max_side in IMAGE_WEBP_SPECS
        if model_label == label
    ]


def iter_webp_targets() -> list[tuple[type[models.Model], str, int]]:
    """Розгорнутий реєстр для сигналів і management-команди."""
    result: list[tuple[type[models.Model], str, int]] = []
    for model_label, field_name, max_side in IMAGE_WEBP_SPECS:
        model = apps.get_model(model_label)
        result.append((model, field_name, max_side))
    return result
