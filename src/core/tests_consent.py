from django.test import TestCase
from django.urls import reverse


class CookieBannerAndCspTests(TestCase):
    def test_banner_and_consent_script_on_home(self):
        response = self.client.get(reverse("catalog:home"))
        self.assertContains(response, "data-cookie-banner")
        self.assertContains(response, "consent.js")
        self.assertContains(response, "Налаштування cookies")
        self.assertContains(response, "data-consent-accept")

    def test_csp_allows_google_ads_hosts(self):
        response = self.client.get(reverse("catalog:home"))
        csp = response.headers.get("Content-Security-Policy", "")
        self.assertIn("https://ad.doubleclick.net", csp)
        self.assertIn("https://www.googleadservices.com", csp)
        self.assertIn("https://www.google.com", csp)
        self.assertIn("https://analytics.google.com", csp)
