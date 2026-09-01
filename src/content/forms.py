from django import forms
from django.utils.translation import gettext_lazy as _

from .models import NewsletterLead


class NewsletterSubscribeForm(forms.Form):
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={
            "class": "form-control", "placeholder": _("Ваш email"), "autocomplete": "email",
        }),
    )
    source = forms.ChoiceField(choices=NewsletterLead.Source.choices, widget=forms.HiddenInput, required=False)
