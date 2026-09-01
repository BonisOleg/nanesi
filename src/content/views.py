from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView

from src.seo.models import SeoLandingPage
from src.seo.views import render_landing

from . import services
from .forms import NewsletterSubscribeForm
from .models import BlogPost, NewsletterLead, SiteSettings, StaticPage

# Дефолти з мокапу (static/css/tokens.css) — якщо в SiteSettings колір не задано.
DEFAULT_ACCENT_COLOR = "#C99B9B"
DEFAULT_ACCENT_HOVER_COLOR = "#A97878"


class PageDetailView(DetailView):
    """Про нас / Доставка і оплата / Оферта / Політика — одна модель, слаг з ТЗ.

    Той самий catch-all (один сегмент URL) також обслуговує SEO-лендінги
    (Підетап 4) — статичні сторінки й лендінги мають спільний неймспейс адрес,
    щоб не заводити другий конкуруючий catch-all."""

    model = StaticPage
    template_name = "content/page_detail.html"
    context_object_name = "page"

    def get_queryset(self):
        return StaticPage.objects.filter(is_published=True)

    def get_object(self, queryset=None):
        slug = self.kwargs["slug"]
        try:
            return get_object_or_404(self.get_queryset(), slug=slug)
        except Http404:
            landing = SeoLandingPage.objects.filter(is_active=True, path=slug).first()
            if landing is None:
                raise
            self._landing = landing
            return landing

    def render_to_response(self, context, **response_kwargs):
        landing = getattr(self, "_landing", None)
        if landing is not None:
            return render_landing(self.request, landing)
        return super().render_to_response(context, **response_kwargs)


class BlogListView(ListView):
    model = BlogPost
    template_name = "content/blog_list.html"
    context_object_name = "posts"
    paginate_by = 12

    def get_queryset(self):
        return BlogPost.objects.filter(is_published=True).order_by("-published_at", "-created_at")


class BlogDetailView(DetailView):
    model = BlogPost
    template_name = "content/blog_detail.html"
    context_object_name = "post"

    def get_queryset(self):
        return BlogPost.objects.filter(is_published=True)

    def get_object(self, queryset=None):
        obj = get_object_or_404(self.get_queryset(), slug=self.kwargs["slug"])
        return obj


def theme_css(request):
    """Кольори акценту з адмінки (SiteSettings) — CSS custom properties, а не інлайн
    <style>, щоб не порушувати CSP style-src 'self' (без 'unsafe-inline')."""
    settings_ = SiteSettings.load()
    accent = settings_.accent_color or DEFAULT_ACCENT_COLOR
    accent_hover = settings_.accent_hover_color or DEFAULT_ACCENT_HOVER_COLOR
    css = f":root {{\n  --color-accent: {accent};\n  --color-accent-hover: {accent_hover};\n}}\n"
    response = HttpResponse(css, content_type="text/css")
    # no-store, не no-cache: файл дешевий (1 запит у SiteSettings), а зміна кольору
    # в адмінці має бути видна відразу, без застарілої кеш-копії в браузері.
    response["Cache-Control"] = "no-store"
    return response


@require_POST
def newsletter_subscribe(request):
    """Popup/інлайн-блок (лист Nanesi п.10) — HTMX: outerHTML-заміна форми на успіх/помилку."""
    form = NewsletterSubscribeForm(request.POST)
    source = request.POST.get("source") or NewsletterLead.Source.POPUP
    if not form.is_valid():
        return render(request, "partials/_newsletter_form.html", {"form": form, "source": source})

    lead = services.subscribe_email(form.cleaned_data["email"], source=form.cleaned_data.get("source") or source)
    return render(request, "partials/_newsletter_success.html", {"lead": lead})
