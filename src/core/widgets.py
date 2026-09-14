"""Віджети адмінки (TinyMCE з нормалізацією переносів)."""
from tinymce.widgets import TinyMCE

from src.core.richtext import normalize_richtext_newlines


class NanesiTinyMCE(TinyMCE):
    """TinyMCE: Enter → ``<br>``, а «голі» ``\\n`` нормалізуються при load/save."""

    def format_value(self, value):
        value = super().format_value(value)
        if value in (None, ""):
            return value
        return normalize_richtext_newlines(value)

    def value_from_datadict(self, data, files, name):
        value = super().value_from_datadict(data, files, name)
        if value is None:
            return value
        return normalize_richtext_newlines(value)
