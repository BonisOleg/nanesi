from django.test import SimpleTestCase

from src.catalog.templatetags.product_grid import pick_grid_columns


class PickGridColumnsTests(SimpleTestCase):
    def test_mobile_always_two(self):
        self.assertEqual(pick_grid_columns(7, mobile=True), 2)
        self.assertEqual(pick_grid_columns(0, mobile=True), 2)

    def test_small_counts(self):
        self.assertEqual(pick_grid_columns(0), 2)
        self.assertEqual(pick_grid_columns(1), 3)
        self.assertEqual(pick_grid_columns(2), 3)

    def test_exact_division(self):
        self.assertEqual(pick_grid_columns(5), 3)
        self.assertEqual(pick_grid_columns(8), 4)
        self.assertEqual(pick_grid_columns(9), 3)
        self.assertEqual(pick_grid_columns(10), 4)
        self.assertEqual(pick_grid_columns(12), 4)

    def test_incomplete_last_row_centered(self):
        """7 → 4+3; 11 → 4+4+3; 13/14 → 3 (макс. 4 кол.)."""
        self.assertEqual(pick_grid_columns(7), 4)
        self.assertEqual(pick_grid_columns(11), 4)
        self.assertEqual(pick_grid_columns(13), 3)
        self.assertEqual(pick_grid_columns(14), 4)
        self.assertEqual(pick_grid_columns(6), 3)
