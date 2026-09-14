from django.test import SimpleTestCase

from src.core.richtext import normalize_richtext_newlines


class NormalizeRichtextNewlinesTests(SimpleTestCase):
    def test_empty(self):
        self.assertEqual(normalize_richtext_newlines(None), "")
        self.assertEqual(normalize_richtext_newlines(""), "")

    def test_plain_single_newline(self):
        self.assertEqual(
            normalize_richtext_newlines("рядок1\nрядок2"),
            "<p>рядок1<br>рядок2</p>",
        )

    def test_plain_paragraph_break(self):
        self.assertEqual(
            normalize_richtext_newlines("абзац1\n\nабзац2"),
            "<p>абзац1</p><p>абзац2</p>",
        )

    def test_html_inner_newline(self):
        self.assertEqual(
            normalize_richtext_newlines("<p>a\nb</p>"),
            "<p>a<br>b</p>",
        )

    def test_html_pretty_print_between_tags(self):
        self.assertEqual(
            normalize_richtext_newlines("<p>a</p>\n<p>b</p>"),
            "<p>a</p><p>b</p>",
        )

    def test_already_ok_unchanged(self):
        html = "<p>a<br>b</p>"
        self.assertEqual(normalize_richtext_newlines(html), html)

    def test_crlf(self):
        self.assertEqual(
            normalize_richtext_newlines("a\r\nb"),
            "<p>a<br>b</p>",
        )
