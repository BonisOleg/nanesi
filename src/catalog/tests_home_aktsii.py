"""Плитка «Акції» на головній: фото колекції aktsii або static sale.webp."""
import tempfile
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import translation
from PIL import Image

from src.catalog.models import Category, Collection


def _tiny_png() -> SimpleUploadedFile:
    buf = BytesIO()
    Image.new("RGB", (2, 2), (180, 40, 40)).save(buf, format="PNG")
    return SimpleUploadedFile("aktsii.png", buf.getvalue(), content_type="image/png")


class HomeAktsiiImageTests(TestCase):
    def setUp(self):
        self._media = tempfile.TemporaryDirectory()
        self._media_override = override_settings(MEDIA_ROOT=self._media.name)
        self._media_override.enable()
        Category.objects.create(name="Сироватки", slug="syrovatky", is_active=True)

    def tearDown(self):
        self._media_override.disable()
        self._media.cleanup()

    def _get_home(self):
        """Запит українською: попередній тест може лишити активною en."""
        with translation.override("uk"):
            aktsii_href = reverse("catalog:collection_detail", kwargs={"slug": "aktsii"})
            response = self.client.get(reverse("catalog:home"))
        return response, aktsii_href

    def _assert_aktsii_tile(self, response, aktsii_href):
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'class="cat-circle" href="{aktsii_href}"')

    def test_tile_uses_collection_image_when_set(self):
        collection = Collection.objects.create(
            name="Акції",
            slug="aktsii",
            kind=Collection.Kind.SALE,
            image=_tiny_png(),
        )
        collection.refresh_from_db()
        response, aktsii_href = self._get_home()
        self._assert_aktsii_tile(response, aktsii_href)
        self.assertContains(response, collection.image.url)
        self.assertNotContains(response, "img/categories/sale.webp")

    def test_tile_falls_back_to_static_when_image_missing(self):
        Collection.objects.create(name="Акції", slug="aktsii", kind=Collection.Kind.SALE)
        response, aktsii_href = self._get_home()
        self._assert_aktsii_tile(response, aktsii_href)
        self.assertContains(response, "img/categories/sale.webp")
