"""Імпорт прайсу CSV/XLSX (замінник живого API-фіду на етапі 1)."""
import io
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from openpyxl import Workbook

from src.catalog.models import Brand, Category, Product, ProductVariant, Supplier
from src.catalog.parsers import parse_csv, parse_xlsx, parse_supplier_file
from src.catalog.services.imports import import_supplier_file

EXAMPLE_DIR = Path(settings.BASE_DIR) / "static" / "examples" / "supplier"


def _xlsx_bytes(headers: list[str], rows: list[list]) -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(headers)
    for row in rows:
        sheet.append(row)
    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


class ParseSupplierFileTests(TestCase):
    def test_csv_aliases_and_semicolon(self):
        raw = (
            "Артикул;Назва;Ціна;Залишок;Категорія;Бренд\n"
            "000005739;Крем PDRN;620;10;Креми;whocares\n"
        ).encode("utf-8-sig")
        rows = parse_csv(raw)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["sku"], "000005739")
        self.assertEqual(rows[0]["name"], "Крем PDRN")
        self.assertEqual(rows[0]["price"], "620")
        self.assertEqual(rows[0]["stock"], "10")
        self.assertEqual(rows[0]["brand"], "whocares")

    def test_xlsx_float_sku_cleaned(self):
        raw = _xlsx_bytes(
            ["SKU", "Name", "Price", "Stock"],
            [[21000401.0, "Item", 100, 3]],
        )
        uploaded = SimpleUploadedFile("price.xlsx", raw)
        rows = parse_xlsx(io.BytesIO(raw))
        self.assertEqual(rows[0]["sku"], "21000401")
        self.assertEqual(parse_supplier_file(uploaded)[0]["sku"], "21000401")


class ImportSupplierFileTests(TestCase):
    def setUp(self):
        self.supplier = Supplier.objects.create(name="Cosmetics Factory")
        self.brand = Brand.objects.create(name="whocares", slug="whocares")
        self.category = Category.objects.create(name="Креми для обличчя", slug="krems")

    def _csv(self, body: str, name: str = "price.csv") -> SimpleUploadedFile:
        return SimpleUploadedFile(name, body.encode("utf-8"))

    def test_creates_sku_cost_and_initial_retail(self):
        uploaded = self._csv(
            "sku,name,price,stock,category,brand\n"
            "000005739,Крем PDRN,620,12,Креми для обличчя,whocares\n"
        )
        report = import_supplier_file(supplier=self.supplier, uploaded_file=uploaded)
        self.assertEqual(report.created, 1)
        variant = ProductVariant.objects.get(sku="000005739")
        self.assertEqual(variant.cost_price, Decimal("620"))
        self.assertEqual(variant.retail_price, Decimal("620"))
        self.assertEqual(variant.stock_quantity, 12)
        self.assertEqual(variant.product.supplier, self.supplier)
        self.assertEqual(variant.product.brand, self.brand)
        self.assertEqual(variant.product.category, self.category)

    def test_update_does_not_overwrite_retail_price(self):
        product = Product.objects.create(
            name="Крем PDRN",
            slug="krem-pdrn",
            brand=self.brand,
            category=self.category,
            supplier=self.supplier,
        )
        ProductVariant.objects.create(
            product=product,
            sku="000005739",
            cost_price=Decimal("620"),
            retail_price=Decimal("844"),
            stock_quantity=5,
        )
        uploaded = self._csv(
            "sku,name,price,stock,brand\n"
            "000005739,Крем PDRN,700,2,whocares\n"
        )
        report = import_supplier_file(supplier=self.supplier, uploaded_file=uploaded)
        self.assertEqual(report.updated, 1)
        variant = ProductVariant.objects.get(sku="000005739")
        self.assertEqual(variant.cost_price, Decimal("700"))
        self.assertEqual(variant.retail_price, Decimal("844"))
        self.assertEqual(variant.stock_quantity, 2)

    def test_skips_duplicate_and_new_without_brand(self):
        uploaded = self._csv(
            "sku,name,price,stock,brand\n"
            "A1,Товар,100,1,whocares\n"
            "A1,Дубль,100,1,whocares\n"
            "A2,Без бренду,100,1,\n"
        )
        report = import_supplier_file(supplier=self.supplier, uploaded_file=uploaded)
        self.assertEqual(report.created, 1)
        self.assertEqual(report.skipped, 2)
        self.assertEqual(ProductVariant.objects.filter(sku="A1").count(), 1)
        self.assertFalse(ProductVariant.objects.filter(sku="A2").exists())


class ExampleSupplierPriceFilesTests(TestCase):
    """Приклади на сторінці «Імпорт прайсу» — парсяться тими ж правилами."""

    EXPECTED_SKUS = {
        "000005739",
        "8809563100316",
        "8809563102600",
        "000005720",
        "8809563103355",
        "8809563103362",
        "8809563103379",
    }

    def test_example_csv_parses(self):
        path = EXAMPLE_DIR / "pryklad-praisu.csv"
        self.assertTrue(path.is_file(), path)
        rows = parse_csv(path.read_bytes())
        self.assertEqual({row["sku"] for row in rows}, self.EXPECTED_SKUS)
        cream = next(row for row in rows if row["sku"] == "000005739")
        self.assertEqual(cream["price"], "620.00")
        self.assertEqual(cream["brand"], "WhoCares")

    def test_example_xlsx_parses(self):
        path = EXAMPLE_DIR / "pryklad-praisu.xlsx"
        self.assertTrue(path.is_file(), path)
        uploaded = SimpleUploadedFile("pryklad-praisu.xlsx", path.read_bytes())
        rows = parse_supplier_file(uploaded)
        self.assertEqual({row["sku"] for row in rows}, self.EXPECTED_SKUS)
        cream = next(row for row in rows if row["sku"] == "000005739")
        self.assertEqual(Decimal(cream["price"]), Decimal("620"))
        self.assertEqual(cream["stock"], "25")
