"""Нормалізація переносів рядків у HTML TinyMCE (admin → вітрина)."""
from __future__ import annotations

import re

_BLOCK_HINT = re.compile(r"<(?:p|br|div|li|h[1-6]|ul|ol|table)\b", re.I)
_TAG_SPLIT = re.compile(r"(<[^>]+>)")


def normalize_richtext_newlines(value: str | None) -> str:
    """Перетворює «голі» \\n на HTML-переноси, не чіпаючи структуру тегів.

    - plain text → ``<p>…</p>`` з ``<br>`` всередині абзацу;
    - HTML → ``\\n`` лише в текстових вузлах (не між тегами) → ``<br>``.
    """
    if not value:
        return ""
    text = value.replace("\r\n", "\n").replace("\r", "\n")
    if "\n" not in text:
        return value

    if not _BLOCK_HINT.search(text):
        paras = re.split(r"\n{2,}", text.strip())
        return "".join(
            "<p>" + para.replace("\n", "<br>") + "</p>"
            for para in paras
            if para != ""
        )

    parts = _TAG_SPLIT.split(text)
    out: list[str] = []
    for part in parts:
        if not part:
            continue
        if part.startswith("<"):
            out.append(part)
            continue
        if part.strip() == "":
            out.append(part.replace("\n", ""))
            continue
        out.append(part.replace("\n", "<br>"))
    return "".join(out)
