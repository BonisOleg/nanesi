"""Міксин honeypot-пастки для публічних форм."""
from django import forms

HONEYPOT_FIELD_NAME = "website"


class HoneypotFormMixin:
    """Поле website ховається CSS-пасткою; боти його заповнюють, люди — ні."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields[HONEYPOT_FIELD_NAME] = forms.CharField(
            required=False,
            label="Website",
            widget=forms.TextInput(attrs={
                "class": "hp-field",
                "autocomplete": "off",
                "tabindex": "-1",
                "aria-hidden": "true",
            }),
        )

    def honeypot_triggered(self) -> bool:
        data = getattr(self, "data", None)
        if not data:
            return False
        return bool(str(data.get(HONEYPOT_FIELD_NAME) or "").strip())
