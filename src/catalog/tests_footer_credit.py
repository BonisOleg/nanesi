"""Кредит PrometeyLabs у футері (footer_developer_links_skill)."""
from django.test import TestCase
from django.urls import reverse

CREDIT_URL = "https://www.prometeylabs.com/internet-shop-v2/"


class FooterDeveloperLinkTests(TestCase):
    def test_home_has_nofollow_credit_link(self):
        response = self.client.get(reverse("catalog:home"))
        self.assertContains(response, CREDIT_URL)
        self.assertContains(response, "nofollow")
        self.assertContains(response, ">PrometeyLabs</a>")
        self.assertContains(response, 'rel="nofollow noopener noreferrer"')

    def test_localized_home_keeps_credit_link(self):
        for path in ("/ru/", "/en/"):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, CREDIT_URL)
                self.assertContains(response, ">PrometeyLabs</a>")

    def test_inner_pages_show_credit_without_link(self):
        for url in (reverse("catalog:catalog"), reverse("catalog:search") + "?q=test"):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "PrometeyLabs")
                self.assertNotContains(response, CREDIT_URL)
                self.assertNotContains(response, "site-footer__credit-link")
