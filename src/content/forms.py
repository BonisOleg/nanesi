from django import forms
from django.utils.translation import gettext_lazy as _

from src.core.forms import HoneypotFormMixin

from .models import NewsletterLead


class NewsletterSubscribeForm(HoneypotFormMixin, forms.Form):
    email = forms.EmailField(
        label="Email",
        max_length=254,
        widget=forms.EmailInput(attrs={
            "class": "form-control",
            "placeholder": _("Ваш email"),
            "autocomplete": "email",
            "maxlength": "254",
        }),
    )
    source = forms.ChoiceField(choices=NewsletterLead.Source.choices, widget=forms.HiddenInput, required=False)

    def clean_email(self):
        return (self.cleaned_data.get("email") or "").strip().lower()
