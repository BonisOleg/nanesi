"""Ручний імпорт прайсу постачальника з адмінки (supplier_admin_file_import_skill).

Інваріант ціни (Доповнення §1): при ОНОВЛЕННІ існуючого SKU роздрібна ціна
(retail_price) НЕ перезаписується файлом — stock_quantity + cost_price (колонка Ціна = закупівля). Роздрібна ціна
задається вручну і оновлюється лише через окремий markup-механізм (Етап C).
Атрибути/фото цим імпортом НЕ пишуться (Правило 9 скіла) — окремий етап.
"""
import logging
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation

from django.db import IntegrityError, transaction
from django.utils.text import slugify

from src.catalog.models import Brand, Category, Product, ProductVariant, Supplier
from src.catalog.parsers import parse_supplier_file

logger = logging.getLogger(__name__)

FALLBACK_CATEGORY_SLUG = "import-bez-kategorii"


class ImportError(Exception):
    """Помилка рівня файлу (не окремого рядка) — невірний формат, немає SKU-колонки тощо."""


@dataclass
class ImportReport:
    created: int = 0
    updated: int = 0
    skipped: int = 0
    fallback_category_used: int = 0
    errors: list[dict] = field(default_factory=list)


def _get_fallback_category() -> Category:
    category, _created = Category.objects.get_or_create(
        slug=FALLBACK_CATEGORY_SLUG,
        defaults={"name": "Імпорт / Без категорії", "is_active": False, "sort_order": 9999},
    )
    return category


def _resolve_category(name: str, report: ImportReport) -> Category:
    if not name:
        report.fallback_category_used += 1
        return _get_fallback_category()
    match = (
        Category.objects.filter(name__iexact=name, is_active=True).first()
        or Category.objects.filter(name__iexact=name).exclude(slug=FALLBACK_CATEGORY_SLUG).first()
    )
    if match is None:
        report.fallback_category_used += 1
        return _get_fallback_category()
    return match


def _resolve_brand(name: str) -> Brand | None:
    if not name:
        return None
    return (
        Brand.objects.filter(name__iexact=name, is_active=True).first()
        or Brand.objects.filter(name__iexact=name).first()
    )


def _parse_decimal(raw: str) -> Decimal | None:
    cleaned = raw.replace(",", ".").replace(" ", "").replace("₴", "").replace("грн", "")
    try:
        value = Decimal(cleaned)
    except InvalidOperation:
        return None
    return value if value >= 0 else None


def _parse_stock(raw: str) -> int:
    try:
        return max(0, int(float(raw.replace(",", "."))))
    except (ValueError, TypeError):
        return 0


@transaction.atomic
def import_supplier_file(*, supplier: Supplier, uploaded_file, name_locale: str = "uk") -> ImportReport:
    try:
        rows = parse_supplier_file(uploaded_file)
    except ValueError as exc:
        raise ImportError(str(exc)) from exc

    if not rows:
        raise ImportError("Файл порожній або немає колонки SKU/Артикул")

    report = ImportReport()
    seen_skus: set[str] = set()

    for index, row in enumerate(rows, start=2):  # рядок у файлі (1 — заголовок)
        sku = row.get("sku", "").strip()
        if not sku:
            report.errors.append({"row": index, "sku": "", "problem": "Немає SKU", "hint": "Заповніть колонку SKU/Артикул"})
            report.skipped += 1
            continue
        if sku in seen_skus:
            report.errors.append({"row": index, "sku": sku, "problem": "Дубль SKU у файлі", "hint": "Прибрати повторний рядок"})
            report.skipped += 1
            continue
        seen_skus.add(sku)

        try:
            with transaction.atomic():  # savepoint — помилка одного рядка не валить файл
                _persist_row(supplier, row, name_locale, report)
        except IntegrityError as exc:
            logger.exception("Помилка БД при імпорті SKU=%s", sku)
            report.errors.append({"row": index, "sku": sku, "problem": f"Помилка БД: {exc}", "hint": "Перевірте унікальність SKU"})
            report.skipped += 1

    return report


def _persist_row(supplier: Supplier, row: dict, name_locale: str, report: ImportReport) -> None:
    sku = row["sku"]
    name = row.get("name", "").strip()
    price_raw = row.get("price", "").strip()
    stock_raw = row.get("stock", "").strip()
    category_name = row.get("category", "").strip()
    brand_name = row.get("brand", "").strip()
    description = row.get("description", "").strip()

    variant = ProductVariant.objects.select_related("product").filter(sku=sku).first()

    if variant is not None:
        update_fields: list[str] = []
        if stock_raw:
            variant.stock_quantity = _parse_stock(stock_raw)
            update_fields.append("stock_quantity")
        # Колонка price у прайсі постачальника = закупівля (cost), НЕ РРЦ.
        if price_raw:
            cost = _parse_decimal(price_raw)
            if cost is not None:
                variant.cost_price = cost
                update_fields.append("cost_price")
        if update_fields:
            update_fields.append("updated_at")
            variant.save(update_fields=update_fields)
        product = variant.product
        product.supplier = supplier
        if name:
            setattr(product, f"name_{name_locale}", name)
        if description:
            setattr(product, f"description_{name_locale}", description)
        product.save()
        report.updated += 1
        return

    if not name:
        report.errors.append({"row": "—", "sku": sku, "problem": "Новий SKU без назви", "hint": "Заповніть колонку Назва для нового товару"})
        report.skipped += 1
        return

    price = _parse_decimal(price_raw) if price_raw else None
    if price is None:
        report.errors.append({"row": "—", "sku": sku, "problem": "Новий SKU без коректної ціни", "hint": "Заповніть колонку Ціна числом"})
        report.skipped += 1
        return

    brand = _resolve_brand(brand_name)
    if brand is None:
        hint = (
            f"Бренд «{brand_name}» не знайдено в довіднику — додайте бренд в адмінці й повторіть імпорт"
            if brand_name else "Заповніть колонку Бренд для нового товару"
        )
        report.errors.append({"row": "—", "sku": sku, "problem": "Новий SKU без бренду", "hint": hint})
        report.skipped += 1
        return

    category = _resolve_category(category_name, report)

    product = Product(
        slug=slugify(f"{name}-{sku}", allow_unicode=True)[:500],
        brand=brand,
        category=category,
        supplier=supplier,
    )
    setattr(product, f"name_{name_locale}", name)
    if description:
        setattr(product, f"description_{name_locale}", description)
    product.save()

    ProductVariant.objects.create(
        product=product,
        sku=sku,
        cost_price=price,
        retail_price=price,  # стартова РРЦ = закупка; далі тільки markup/ручне
        stock_quantity=_parse_stock(stock_raw) if stock_raw else 0,
    )
    report.created += 1
