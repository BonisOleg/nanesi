"""Тести WebP-конвертації ImageField."""
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from PIL import Image

from src.catalog.forms import ReviewForm
from src.catalog.models import Brand, Category, Product, ProductImage, Supplier
from src.core.utils.images import MAX_UPLOAD_BYTES, validate_image
from django.core.exceptions import ValidationError


def _make_png(width: int = 100, height: int = 80, color=(200, 100, 50)) -> SimpleUploadedFile:
    buf = BytesIO()
    Image.new("RGB", (width, height), color).save(buf, format="PNG")
    return SimpleUploadedFile("test-photo.png", buf.getvalue(), content_type="image/png")


class ValidateImageTests(TestCase):
    def test_rejects_bad_extension(self):
        f = SimpleUploadedFile("shell.php", b"<?php", content_type="application/x-php")
        with self.assertRaises(ValidationError):
            validate_image(f)

    def test_accepts_png(self):
        validate_image(_make_png())

    def test_rejects_over_5mb(self):
        f = SimpleUploadedFile(
            "huge.png",
            b"x" * (MAX_UPLOAD_BYTES + 1),
            content_type="image/png",
        )
        with self.assertRaises(ValidationError):
            validate_image(f)


class ReviewPhotoLimitTests(TestCase):
    def test_form_rejects_over_5mb(self):
        form = ReviewForm(
            data={
                "rating": "5",
                "text": "Достатньо довгий текст відгуку",
                "author_name": "Гість",
            },
            files={
                "photos": SimpleUploadedFile(
                    "huge.png",
                    b"x" * (MAX_UPLOAD_BYTES + 1),
                    content_type="image/png",
                ),
            },
            is_authenticated=False,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("photos", form.errors)


class WebpConvertOnSaveTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Test Cat", slug="test-cat")
        self.brand = Brand.objects.create(name="Test Brand", slug="test-brand")
        self.supplier = Supplier.objects.create(name="Test Supplier")
        self.product = Product.objects.create(
            name="Test Product",
            slug="test-product",
            category=self.category,
            brand=self.brand,
            supplier=self.supplier,
        )

    def test_product_image_becomes_webp(self):
        img = ProductImage.objects.create(
            product=self.product,
            image=_make_png(400, 300),
            is_main=True,
        )
        img.refresh_from_db()
        self.assertTrue(img.image.name.lower().endswith(".webp"))
        with Image.open(img.image.path) as opened:
            self.assertEqual(opened.format, "WEBP")
            self.assertEqual(opened.size, (400, 300))

    def test_oversized_resized(self):
        img = ProductImage.objects.create(
            product=self.product,
            image=_make_png(2000, 1500),
        )
        img.refresh_from_db()
        with Image.open(img.image.path) as opened:
            self.assertEqual(opened.format, "WEBP")
            self.assertLessEqual(max(opened.size), 800)

    def test_brand_logo_not_converted(self):
        self.brand.logo = _make_png(200, 200)
        self.brand.save()
        self.brand.refresh_from_db()
        self.assertTrue(self.brand.logo.name.lower().endswith(".png"))
