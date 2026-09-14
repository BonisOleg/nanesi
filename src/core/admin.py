"""Спільні міксини адмінки (admin_skill: Unfold + TinyMCE)."""
from src.core.widgets import NanesiTinyMCE


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
