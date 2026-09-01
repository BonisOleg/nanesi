from django import forms
from django.utils.translation import gettext_lazy as _

from src.commerce.models import Order
from src.commerce.selectors import available_delivery_methods, available_payment_methods


class CheckoutForm(forms.Form):
    full_name = forms.CharField(label="ПІБ", max_length=255)
    phone = forms.CharField(label="Телефон", max_length=20)
    email = forms.EmailField(label="Email", required=False)

    delivery_method = forms.ChoiceField(label="Спосіб доставки", choices=())
    np_city_name = forms.CharField(label="Місто", max_length=255, required=False)
    np_city_ref = forms.CharField(widget=forms.HiddenInput, max_length=64, required=False)
    np_warehouse_name = forms.CharField(label="Відділення", max_length=255, required=False)
    np_warehouse_ref = forms.CharField(widget=forms.HiddenInput, max_length=64, required=False)
    ukrposhta_address = forms.CharField(label="Адреса (Укрпошта)", max_length=512, required=False)

    payment_method = forms.ChoiceField(label="Спосіб оплати", choices=())
    comment = forms.CharField(label="Коментар", widget=forms.Textarea, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["delivery_method"].choices = available_delivery_methods()
        self.fields["payment_method"].choices = available_payment_methods()

    def clean(self):
        cleaned = super().clean()
        delivery_method = cleaned.get("delivery_method")

        if delivery_method in (Order.DeliveryMethod.NOVA_POSHTA_WAREHOUSE, Order.DeliveryMethod.NOVA_POSHTA_COURIER):
            if not cleaned.get("np_city_name"):
                self.add_error("np_city_name", _("Вкажіть місто"))
            if delivery_method == Order.DeliveryMethod.NOVA_POSHTA_WAREHOUSE and not cleaned.get("np_warehouse_name"):
                self.add_error("np_warehouse_name", _("Вкажіть відділення"))
        elif delivery_method == Order.DeliveryMethod.UKRPOSHTA:
            if not cleaned.get("ukrposhta_address"):
                self.add_error("ukrposhta_address", _("Вкажіть адресу доставки"))

        return cleaned
