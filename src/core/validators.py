"""Спільна валідація публічного вводу: телефон UA, ПІБ, JSON у HTML."""
import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

PHONE_STORED_RE = re.compile(r"^380\d{9}$")
PERSON_NAME_RE = re.compile(
    r"^[A-Za-zА-Яа-яЁёІіЇїЄєҐґ'’\- ]+$",
)
PERSON_NAME_LETTER_RE = re.compile(r"[A-Za-zА-Яа-яЁёІіЇїЄєҐґ]")
PERSON_NAME_HTML_PATTERN = r"[A-Za-zА-Яа-яЁёІіЇїЄєҐґ'’\- ]{2,255}"
PHONE_HTML_PATTERN = r"[\d+\s\-()]{9,20}"

PHONE_ERROR = _("Формат телефону: 380XXXXXXXXX, +380… або 0XXXXXXXXX")
NAME_ERROR = _("Ім'я може містити лише літери, пробіл, дефіс і апостроф")
NAME_SHORT_ERROR = _("Вкажіть ім'я (щонайменше 2 символи)")


def normalize_ua_phone(value: str) -> str:
    """Приймає +380 / 0XX / пробіли / дефіси, зберігає як 380XXXXXXXXX."""
    digits = re.sub(r"\D", "", value or "")
    if digits.startswith("380") and len(digits) == 12:
        normalized = digits
    elif digits.startswith("0") and len(digits) == 10:
        normalized = "38" + digits
    elif len(digits) == 9:
        normalized = "380" + digits
    else:
        raise ValidationError(PHONE_ERROR)
    if not PHONE_STORED_RE.fullmatch(normalized):
        raise ValidationError(PHONE_ERROR)
    return normalized


def validate_person_name(value: str, *, min_length: int = 2, max_length: int = 255) -> str:
    name = " ".join((value or "").split())
    if len(name) < min_length:
        raise ValidationError(NAME_SHORT_ERROR)
    if len(name) > max_length:
        raise ValidationError(_("Ім'я занадто довге"))
    if not PERSON_NAME_RE.fullmatch(name) or not PERSON_NAME_LETTER_RE.search(name):
        raise ValidationError(NAME_ERROR)
    return name


def escape_json_for_html(payload: str) -> str:
    """Щоб JSON у <script> не зламав розмітку через </script> у назві товару."""
    return payload.replace("<", "\\u003c")
