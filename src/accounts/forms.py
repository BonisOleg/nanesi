"""Форми кабінету: одна форма вхід/реєстрація за телефоном або email (Відповіді п.6)."""
import uuid

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import PasswordResetForm as DjangoPasswordResetForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from src.accounts.models import User
from src.core.forms import HoneypotFormMixin
from src.core.validators import (
    PERSON_NAME_HTML_PATTERN,
    PHONE_HTML_PATTERN,
    normalize_ua_phone,
    validate_person_name,
)


def _widget(**attrs):
    attrs.setdefault("class", "form-control")
    return attrs


class LoginForm(HoneypotFormMixin, AuthenticationForm):
    username = forms.CharField(
        label=_("Телефон або email"),
        max_length=254,
        widget=forms.TextInput(attrs=_widget(
            autofocus=True, autocomplete="username", maxlength="254",
        )),
    )
    password = forms.CharField(
        label=_("Пароль"),
        strip=False,
        widget=forms.PasswordInput(attrs=_widget(autocomplete="current-password")),
    )

    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": _("Невірний телефон/email або пароль."),
    }


class RegisterForm(HoneypotFormMixin, forms.Form):
    full_name = forms.CharField(
        label=_("Ім'я"),
        min_length=2,
        max_length=150,
        widget=forms.TextInput(attrs=_widget(
            minlength="2",
            maxlength="150",
            pattern=PERSON_NAME_HTML_PATTERN,
            autocomplete="name",
        )),
    )
    phone = forms.CharField(
        label=_("Телефон"),
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs=_widget(
            placeholder="380XXXXXXXXX",
            inputmode="tel",
            autocomplete="tel",
            maxlength="20",
            pattern=PHONE_HTML_PATTERN,
        )),
    )
    email = forms.EmailField(
        label=_("Email"),
        required=False,
        max_length=254,
        widget=forms.EmailInput(attrs=_widget(autocomplete="email", maxlength="254")),
    )
    password1 = forms.CharField(
        label=_("Пароль"), strip=False,
        widget=forms.PasswordInput(attrs=_widget(autocomplete="new-password")),
    )
    password2 = forms.CharField(
        label=_("Повторіть пароль"), strip=False,
        widget=forms.PasswordInput(attrs=_widget(autocomplete="new-password")),
    )

    def clean_full_name(self):
        return validate_person_name(self.cleaned_data.get("full_name", ""), max_length=150)

    def clean_phone(self):
        phone = self.cleaned_data.get("phone", "").strip()
        if not phone:
            return phone
        phone = normalize_ua_phone(phone)
        if User.objects.filter(phone=phone).exists():
            raise ValidationError(_("Користувач з цим телефоном вже зареєстрований"))
        return phone

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        if not email:
            return email
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError(_("Користувач з цим email вже зареєстрований"))
        return email

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("phone") and not cleaned.get("email"):
            raise ValidationError(_("Вкажіть телефон або email"))
        password1 = cleaned.get("password1")
        password2 = cleaned.get("password2")
        if password1 and password2 and password1 != password2:
            self.add_error("password2", _("Паролі не збігаються"))
        if password1:
            validate_password(password1)
        return cleaned

    def save(self) -> User:
        phone = self.cleaned_data.get("phone") or ""
        email = self.cleaned_data.get("email") or ""
        user = User(
            username=f"u{uuid.uuid4().hex[:20]}",
            first_name=self.cleaned_data["full_name"],
            phone=phone or None,
            email=email,
        )
        user.set_password(self.cleaned_data["password1"])
        user.save()
        return user


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "phone", "email"]
        labels = {"first_name": _("Ім'я"), "last_name": _("Прізвище"), "phone": _("Телефон"), "email": _("Email")}
        widgets = {
            "first_name": forms.TextInput(attrs=_widget(
                minlength="2", maxlength="150", pattern=PERSON_NAME_HTML_PATTERN, autocomplete="given-name",
            )),
            "last_name": forms.TextInput(attrs=_widget(
                minlength="2", maxlength="150", pattern=PERSON_NAME_HTML_PATTERN, autocomplete="family-name",
            )),
            "phone": forms.TextInput(attrs=_widget(
                placeholder="380XXXXXXXXX", inputmode="tel", autocomplete="tel",
                maxlength="20", pattern=PHONE_HTML_PATTERN,
            )),
            "email": forms.EmailInput(attrs=_widget(autocomplete="email", maxlength="254")),
        }

    def clean_first_name(self):
        value = (self.cleaned_data.get("first_name") or "").strip()
        if not value:
            return value
        return validate_person_name(value, max_length=150)

    def clean_last_name(self):
        value = (self.cleaned_data.get("last_name") or "").strip()
        if not value:
            return value
        return validate_person_name(value, max_length=150)

    def clean_phone(self):
        phone = (self.cleaned_data.get("phone") or "").strip()
        if not phone:
            return None
        phone = normalize_ua_phone(phone)
        if User.objects.filter(phone=phone).exclude(pk=self.instance.pk).exists():
            raise ValidationError(_("Цей телефон вже використовується іншим акаунтом"))
        return phone

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if email and User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError(_("Цей email вже використовується іншим акаунтом"))
        return email

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("phone") and not cleaned.get("email"):
            raise ValidationError(_("Вкажіть телефон або email"))
        return cleaned


class SavedWarehouseForm(forms.ModelForm):
    class Meta:
        model = User
        labels = {
            "saved_np_city_name": _("Місто"),
            "saved_np_warehouse_name": _("Відділення / поштомат"),
            "saved_ukrposhta_index": _("Індекс Укрпошти"),
            "saved_ukrposhta_address": _("Адреса / відділення Укрпошти"),
            # Приховані ref: verbose_name в адмінці змінено, на сайті лишається попередній підпис.
            "saved_np_city_ref": "Ref міста (НП)",
            "saved_np_warehouse_ref": "Ref відділення / поштомату (НП)",
        }
        fields = [
            "saved_np_city_name", "saved_np_city_ref",
            "saved_np_warehouse_name", "saved_np_warehouse_ref",
            "saved_ukrposhta_index", "saved_ukrposhta_address",
        ]
        widgets = {
            "saved_np_city_name": forms.TextInput(attrs=_widget(id="id_saved_np_city_name", autocomplete="off")),
            "saved_np_city_ref": forms.HiddenInput(attrs={"id": "id_saved_np_city_ref"}),
            "saved_np_warehouse_name": forms.TextInput(attrs=_widget(id="id_saved_np_warehouse_name", autocomplete="off")),
            "saved_np_warehouse_ref": forms.HiddenInput(attrs={"id": "id_saved_np_warehouse_ref"}),
            "saved_ukrposhta_index": forms.TextInput(attrs=_widget(
                id="id_saved_ukrposhta_index",
                inputmode="numeric",
                autocomplete="postal-code",
                pattern=r"\d{5}",
                maxlength="5",
            )),
            "saved_ukrposhta_address": forms.TextInput(attrs=_widget(
                id="id_saved_ukrposhta_address",
                autocomplete="street-address",
            )),
        }


class PasswordResetForm(HoneypotFormMixin, DjangoPasswordResetForm):
    def save(self, *args, **kwargs):
        if self.honeypot_triggered():
            return
        return super().save(*args, **kwargs)
