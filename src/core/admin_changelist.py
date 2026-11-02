"""ChangeList для select-фільтрів над таблицею."""
from django.contrib.admin.filters import RelatedFieldListFilter
from django.contrib.admin.views.main import ChangeList


class TopFiltersChangeList(ChangeList):
    """У верхньому рядку показуємо FK/M2M-фільтри навіть з одним значенням у списку."""

    def get_filters(self, request):
        if not getattr(self.model_admin, "top_filters", False):
            return super().get_filters(request)

        original_has_output = RelatedFieldListFilter.has_output

        def relaxed_has_output(filter_spec):
            if original_has_output(filter_spec):
                return True
            if len(filter_spec.lookup_choices) >= 1:
                return True
            return False

        RelatedFieldListFilter.has_output = relaxed_has_output
        try:
            return super().get_filters(request)
        finally:
            RelatedFieldListFilter.has_output = original_has_output
