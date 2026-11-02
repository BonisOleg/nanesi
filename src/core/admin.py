"""Спільні міксини адмінки (admin_skill: Unfold + TinyMCE)."""
from src.core.admin_changelist import TopFiltersChangeList
from src.core.widgets import NanesiTinyMCE

_ALL_FILTER_LABELS = frozenset({"All", "Всі", "Усі"})


class TopFiltersAdminMixin:
    """Select-фільтри над таблицею. Бічна панель Unfold для цього списку не рендериться."""

    top_filters = True
    change_list_template = "admin/top_filters_change_list.html"
    filter_title_overrides: dict[str, str] = {}

    def get_changelist(self, request, **kwargs):
        return TopFiltersChangeList

    def get_changelist_instance(self, request):
        cl = super().get_changelist_instance(request)
        overrides = self.filter_title_overrides or {}
        for spec in cl.filter_specs:
            field_path = getattr(spec, "field_path", None) or getattr(spec, "parameter_name", None)
            if field_path in overrides:
                spec.title = overrides[field_path]
            prepared = []
            for choice in spec.choices(cl):
                item = dict(choice)
                if str(item.get("display") or "") in _ALL_FILTER_LABELS:
                    item["display"] = "Усі"
                prepared.append(item)
            spec.top_choices = prepared
        return cl


class TinyMCEAdminMixin:
    """Підключає django-tinymce до перелічених полів (і їх *_uk/*_ru/*_en)."""

    tinymce_fields: tuple[str, ...] = ()

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if self._is_tinymce_field(db_field.name):
            kwargs["widget"] = NanesiTinyMCE(mce_attrs={"height": 360})
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    def _is_tinymce_field(self, name: str) -> bool:
        if name in self.tinymce_fields:
            return True
        return any(
            name.startswith(f"{base}_")
            for base in self.tinymce_fields
        )
