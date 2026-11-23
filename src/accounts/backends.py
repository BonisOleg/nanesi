"""Вхід за телефоном або email + пароль, одна форма (Відповіді п.6, Підетап 2).

`username` лишається обов'язковим полем `AbstractUser` (createsuperuser/адмінка),
але кабінет входить сюди — за номером (`380…` / `0XX` / `+380`) або email."""
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.core.exceptions import ValidationError
from django.db.models import Q

from src.core.validators import normalize_ua_phone


def _phone_lookup(identifier: str) -> str:
    if "@" in identifier:
        return identifier
    try:
        return normalize_ua_phone(identifier)
    except ValidationError:
        return identifier


class PhoneOrEmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        identifier = (username or "").strip()
        if not identifier or not password:
            return None

        User = get_user_model()
        try:
            user = User.objects.get(
                Q(phone=_phone_lookup(identifier)) | Q(email__iexact=identifier),
            )
        except User.DoesNotExist:
            return None
        except User.MultipleObjectsReturned:
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
