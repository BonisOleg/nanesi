"""Прев’ю Instagram на головній: фото з SiteSettings або static fallback."""
import tempfile
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import translation
from PIL import Image

from src.content.models import SiteSettings

_STATIC_FALLBACKS = (
    "img/products/pdrn-cream.webp",
    "img/products/centella-serum.webp",
    "img/products/bb-cushion.webp",
)


def _tiny_png(name: str) -> SimpleUploadedFile:
    buf = BytesIO()
    Image.new("RGB", (8, 8), (180, 40, 40)).save(buf, format="PNG")
    return SimpleUploadedFile(name, buf.getvalue(), content_type="image/png")


class HomeInstagramImageTests(TestCase):
    def setUp(self):
        self._media = tempfile.TemporaryDirectory()
        self._media_override = override_settings(MEDIA_ROOT=self._media.name)
        self._media_override.enable()

    def tearDown(self):
        self._media_override.disable()
        self._media.cleanup()

    def _get_home(self):
        with translation.override("uk"):
            return self.client.get(reverse("catalog:home"))

    def test_ig_preview_falls_back_to_static(self):
        response = self._get_home()
        self.assertEqual(response.status_code, 200)
        for path in _STATIC_FALLBACKS:
            self.assertContains(response, path)

    def test_ig_preview_uses_uploaded_images(self):
        site = SiteSettings.load()
        site.ig_image_1 = _tiny_png("ig-1.png")
        site.ig_image_2 = _tiny_png("ig-2.png")
        site.ig_image_3 = _tiny_png("ig-3.png")
        site.save()
        site.refresh_from_db()

        response = self._get_home()
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, site.ig_image_1.url)
        self.assertContains(response, site.ig_image_2.url)
        self.assertContains(response, site.ig_image_3.url)
        for path in _STATIC_FALLBACKS:
            self.assertNotContains(response, path)
