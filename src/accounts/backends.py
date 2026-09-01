"""Вхід за телефоном або email + пароль, одна форма (Відповіді п.6, Підетап 2).

`username` лишається обов'язковим полем `AbstractUser` (createsuperuser/адмінка),
але кабінет входить сюди — за номером телефону (`380XXXXXXXXX`) або email."""
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q


class PhoneOrEmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        identifier = (username or "").strip()
        if not identifier or not password:
            return None

        User = get_user_model()
        try:
            user = User.objects.get(Q(phone=identifier) | Q(email__iexact=identifier))
        except User.DoesNotExist:
            return None
        except User.MultipleObjectsReturned:
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
