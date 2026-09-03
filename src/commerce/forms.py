import re

from django import forms
from django.utils.translation import gettext_lazy as _

from src.commerce.models import Order
from src.commerce.selectors import available_delivery_methods, available_payment_methods

UKRPOSHTA_INDEX_RE = re.compile(r"^\d{5}$")


class CheckoutForm(forms.Form):
    full_name = forms.CharField(label="ПІБ", max_length=255)
    phone = forms.CharField(label="Телефон", max_length=20)
    email = forms.EmailField(label="Email", required=False)

    delivery_method = forms.ChoiceField(
        label="Спосіб доставки",
        choices=(),
        widget=forms.RadioSelect,
    )
    np_city_name = forms.CharField(label="Місто", max_length=255, required=False)
    np_city_ref = forms.CharField(widget=forms.HiddenInput, max_length=64, required=False)
    np_warehouse_name = forms.CharField(label=_("Відділення / поштомат"), max_length=255, required=False)
    np_warehouse_ref = forms.CharField(widget=forms.HiddenInput, max_length=64, required=False)
    ukrposhta_index = forms.CharField(
        label=_("Індекс"),
        max_length=5,
        required=False,
        widget=forms.TextInput(attrs={
            "inputmode": "numeric",
            "autocomplete": "postal-code",
            "pattern": r"\d{5}",
            "maxlength": "5",
        }),
    )
    ukrposhta_address = forms.CharField(label="Адреса (Укрпошта)", max_length=512, required=False)

    payment_method = forms.ChoiceField(
        label="Спосіб оплати",
        choices=(),
        widget=forms.RadioSelect,
    )
    comment = forms.CharField(
        label="Коментар",
        widget=forms.Textarea(attrs={"rows": 5}),
        required=False,
    )
    privacy_consent = forms.BooleanField(
        label=_("Згода на обробку персональних даних"),
        required=True,
        error_messages={
            "required": _("Потрібна згода на обробку персональних даних"),
        },
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["delivery_method"].choices = available_delivery_methods()
        self.fields["payment_method"].choices = available_payment_methods()
        delivery_choices = self.fields["delivery_method"].choices
        payment_choices = self.fields["payment_method"].choices
        if delivery_choices and not self.is_bound and not self.initial.get("delivery_method"):
            self.initial["delivery_method"] = delivery_choices[0][0]
        if payment_choices and not self.is_bound and not self.initial.get("payment_method"):
            self.initial["payment_method"] = payment_choices[0][0]

    def clean(self):
        cleaned = super().clean()
        delivery_method = cleaned.get("delivery_method")

        if delivery_method == Order.DeliveryMethod.NOVA_POSHTA_WAREHOUSE:
            if not cleaned.get("np_city_name"):
                self.add_error("np_city_name", _("Вкажіть місто"))
            if not cleaned.get("np_warehouse_name"):
                self.add_error("np_warehouse_name", _("Вкажіть відділення або поштомат"))
        elif delivery_method == Order.DeliveryMethod.UKRPOSHTA:
            index = (cleaned.get("ukrposhta_index") or "").strip()
            cleaned["ukrposhta_index"] = index
            if not index:
                self.add_error("ukrposhta_index", _("Вкажіть поштовий індекс"))
            elif not UKRPOSHTA_INDEX_RE.fullmatch(index):
                self.add_error("ukrposhta_index", _("Індекс має містити 5 цифр"))
            if not cleaned.get("ukrposhta_address"):
                self.add_error("ukrposhta_address", _("Вкажіть адресу доставки"))

        return cleaned
