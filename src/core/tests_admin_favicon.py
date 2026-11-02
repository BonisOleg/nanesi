from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class AdminFaviconTests(TestCase):
    def _assert_favicons_in_html(self, html: str) -> None:
        self.assertIn('rel="icon"', html)
        self.assertIn("favicon.ico", html)
        self.assertIn("favicon-32.png", html)
        self.assertIn("favicon-16.png", html)
        self.assertRegex(html, r'rel="apple-touch-icon"[^>]*apple-touch-icon\.png')
        self.assertNotRegex(html, r'favicon[^"\']*\?v=')

    def test_admin_login_has_site_favicons(self):
        response = self.client.get(reverse("admin:login"))
        self.assertEqual(response.status_code, 200)
        self._assert_favicons_in_html(response.content.decode())

    def test_admin_index_has_site_favicons(self):
        user = get_user_model().objects.create_superuser(
            "favicon-admin", "favicon@example.com", "pass-word-1"
        )
        self.client.force_login(user)
        response = self.client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 200)
        self._assert_favicons_in_html(response.content.decode())
