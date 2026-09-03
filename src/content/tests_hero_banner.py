"""Hero-банери головної: queryset / fallback на SiteSettings."""
from django.test import TestCase

from src.catalog.views import _hero_banners_for_home
from src.content.models import HeroBanner, SiteSettings


class HeroBannerQueryTests(TestCase):
    def setUp(self):
        self.site = SiteSettings.load()
        self.site.hero_title = "Тестовий hero"
        self.site.hero_subtitle = "<p>Підзаголовок</p>"
        self.site.site_name = "NANESI"
        self.site.tagline = "BEAUTY"
        self.site.save()
        HeroBanner.objects.all().delete()

    def test_fallback_when_no_banners(self):
        banners = _hero_banners_for_home()
        self.assertEqual(len(banners), 1)
        self.assertEqual(banners[0].title, "Тестовий hero")
        self.assertIn("NANESI", banners[0].eyebrow)

    def test_active_banners_ordered(self):
        HeroBanner.objects.create(title="C", sort_order=3, is_active=True)
        HeroBanner.objects.create(title="A", sort_order=1, is_active=True)
        HeroBanner.objects.create(title="B", sort_order=2, is_active=False)
        titles = [b.title for b in _hero_banners_for_home()]
        self.assertEqual(titles, ["A", "C"])

    def test_seed_shape_three_slides(self):
        for i in range(1, 4):
            HeroBanner.objects.create(
                title=f"Slide {i}",
                sort_order=i,
                is_active=True,
                button_url="/katalog/",
            )
        self.assertEqual(len(_hero_banners_for_home()), 3)
