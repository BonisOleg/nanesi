"""Парсери файлів постачальника: CSV/XLSX → list[dict] з канонічними ключами.

Лише формат/encoding/alias→canonical. Бізнес-валідація (ціна/SKU/бренд) —
у services/imports.py (supplier_admin_file_import_skill, Фаза 2–3).
"""
import csv
import io
from typing import Any

import openpyxl

ALIASES: dict[str, tuple[str, ...]] = {
    "sku": ("sku", "артикул", "код_товара", "код_товару", "vendor_code", "код"),
    "name": ("name", "назва", "название", "найменування", "название_товара", "назва_товару"),
    "price": (
        "price", "цена", "ціна", "цена_рекомендована", "ціна_рекомендована",
        "розничная_цена", "роздрібна_ціна", "цена_рекомендована_роздрібна",
    ),
    "stock": ("stock", "наличие", "наявність", "остаток", "залишок", "qty", "quantity"),
    "category": ("category", "категорія", "категория", "название_группы", "группа", "група"),
    "brand": ("brand", "бренд", "производитель", "виробник"),
    "description": ("description", "описание", "опис", "описание_укр", "опис_укр"),
}


def _normalize_header(raw: str) -> str:
    header = (raw or "").strip().lower().replace("\ufeff", "")
    header = header.replace("-", "_").replace(" ", "_")
    while "__" in header:
        header = header.replace("__", "_")
    return header


def _build_alias_map() -> dict[str, str]:
    mapping: dict[str, str] = {}
    for canonical, aliases in ALIASES.items():
        for alias in aliases:
            mapping[_normalize_header(alias)] = canonical
    return mapping


_ALIAS_MAP = _build_alias_map()


def _clean_sku(text: str) -> str:
    # float SKU з Excel (21000401.0 → 21000401)
    if text.endswith(".0") and text[:-2].isdigit():
        return text[:-2]
    return text


def _map_row(headers: list[str], raw_row: list[Any]) -> dict[str, str]:
    row: dict[str, str] = {}
    for header, value in zip(headers, raw_row):
        canonical = _ALIAS_MAP.get(_normalize_header(header))
        if canonical is None:
            continue
        text = "" if value is None else str(value).strip()
        if canonical == "sku":
            text = _clean_sku(text)
        row[canonical] = text
    return row


def parse_csv(raw_bytes: bytes) -> list[dict[str, str]]:
    text = None
    for encoding in ("utf-8-sig", "utf-8", "cp1251"):
        try:
            text = raw_bytes.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        raise ValueError("Не вдалося визначити кодування CSV-файлу")

    sample = text[:2048]
    delimiter = ";" if sample.count(";") > sample.count(",") else ","
    rows = list(csv.reader(io.StringIO(text), delimiter=delimiter))
    if not rows:
        return []
    headers = rows[0]
    return [_map_row(headers, row) for row in rows[1:] if any(cell.strip() for cell in row)]


def parse_xlsx(file_obj) -> list[dict[str, str]]:
    workbook = openpyxl.load_workbook(file_obj, read_only=True, data_only=True)
    sheet = workbook.worksheets[0]
    rows_iter = sheet.iter_rows(values_only=True)
    try:
        headers = [str(h) if h is not None else "" for h in next(rows_iter)]
    except StopIteration:
        return []
    result: list[dict[str, str]] = []
    for raw_row in rows_iter:
        if not any(cell is not None and str(cell).strip() for cell in raw_row):
            continue
        result.append(_map_row(headers, list(raw_row)))
    return result


def parse_supplier_file(uploaded_file) -> list[dict[str, str]]:
    filename = (getattr(uploaded_file, "name", "") or "").lower()
    if filename.endswith(".xlsx"):
        return parse_xlsx(uploaded_file)
    if filename.endswith(".csv"):
        return parse_csv(uploaded_file.read())
    raise ValueError("Підтримуються лише файли .csv та .xlsx")
