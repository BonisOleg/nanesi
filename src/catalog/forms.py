from django import forms
from django.utils.translation import gettext_lazy as _

MAX_REVIEW_PHOTOS = 5
MAX_REVIEW_PHOTO_SIZE = 8 * 1024 * 1024


def _widget(**attrs):
    attrs.setdefault("class", "form-control")
    return attrs


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    """Django FileField не вміє «з коробки» приймати список файлів навіть з
    allow_multiple_selected=True на віджеті (Django 5+) — потрібен clean() для списку."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            return [single_file_clean(d, initial) for d in data]
        result = single_file_clean(data, initial)
        return [result] if result else []


class ReviewForm(forms.Form):
    """Форма відгуку з фото (Підетап 3, Відповіді п.8) — доступна гостям і
    авторизованим; автору без акаунту потрібне ім'я, фото — до 5 штук."""

    author_name = forms.CharField(
        label=_("Ваше ім'я"), max_length=255, required=False,
        widget=forms.TextInput(attrs=_widget(placeholder=_("Як вас підписати у відгуку"))),
    )
    rating = forms.ChoiceField(
        label=_("Оцінка"),
        choices=[(5, "5"), (4, "4"), (3, "3"), (2, "2"), (1, "1")],
        widget=forms.RadioSelect,
    )
    text = forms.CharField(
        label=_("Текст відгуку"), min_length=10, max_length=3000,
        widget=forms.Textarea(attrs=_widget(rows=5, placeholder=_("Ваші враження від товару"))),
    )
    photos = MultipleFileField(
        label=_("Фото (до 5)"), required=False,
        widget=MultipleFileInput(attrs={
            "multiple": True,
            "accept": "image/*",
            "class": "review-file__input",
            "aria-labelledby": "id_photos-label",
        }),
    )

    def __init__(self, *args, is_authenticated=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_authenticated = is_authenticated
        if not is_authenticated:
            self.fields["author_name"].required = True

    def clean_photos(self):
        files = self.cleaned_data.get("photos") or []
        if len(files) > MAX_REVIEW_PHOTOS:
            raise forms.ValidationError(_("Не більше %(max)s фото") % {"max": MAX_REVIEW_PHOTOS})
        for f in files:
            if f.size > MAX_REVIEW_PHOTO_SIZE:
                raise forms.ValidationError(_("Кожне фото — не більше 8MB"))
        return files


class SupplierImportForm(forms.Form):
    file = forms.FileField(label="Файл (.csv або .xlsx)")
    name_locale = forms.ChoiceField(
        label="Мова назв у файлі",
        choices=[("uk", "Українська"), ("ru", "Російська")],
        initial="uk",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from unfold.widgets import UnfoldAdminSelectWidget

        self.fields["name_locale"].widget = UnfoldAdminSelectWidget()
        self.fields["file"].widget.attrs.update(
            {
                "class": "si-file__input",
                "accept": ".csv,.xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,text/csv",
            }
        )

    def clean_file(self):
        uploaded = self.cleaned_data["file"]
        name = (uploaded.name or "").lower()
        if not (name.endswith(".csv") or name.endswith(".xlsx")):
            raise forms.ValidationError("Підтримуються лише файли .csv та .xlsx")
        if uploaded.size > 15 * 1024 * 1024:
            raise forms.ValidationError("Максимальний розмір файлу — 15MB")
        return uploaded
