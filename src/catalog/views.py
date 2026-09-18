from types import SimpleNamespace

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Avg, Count, Prefetch
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import get_language, gettext as _
from src.core.views_i18n import localize_path
from django.views.decorators.http import require_GET, require_POST

from src.catalog import selectors
from src.catalog.forms import ReviewForm
from src.catalog.models import Brand, Category, Product, ProductAttributeValue
from src.catalog.services import reviews as review_services
from src.content.models import HeroBanner, SiteSettings, TrustBadge
from src.core import analytics

REVIEWS_PER_PAGE = 5


def _query_string_without(request, *drop_keys: str) -> str:
    params = request.GET.copy()
    for key in drop_keys:
        params.pop(key, None)
    return params.urlencode()


def _paginate_reviews(request, product: Product) -> dict:
    """Схвалені відгуки: avg/count по всіх, список — по 5 на сторінку (?reviews_page=)."""
    qs = (
        product.reviews.filter(is_approved=True)
        .select_related("user")
        .prefetch_related("images")
        .order_by("-created_at")
    )
    stats = qs.aggregate(avg=Avg("rating"), cnt=Count("id"))
    paginator = Paginator(qs, REVIEWS_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get("reviews_page"))
    return {
        "reviews": page_obj.object_list,
        "reviews_page": page_obj,
        "reviews_count": stats["cnt"] or 0,
        "rating_avg": stats["avg"],
        "reviews_query_string": _query_string_without(request, "reviews_page"),
    }


def _hero_banners_for_home() -> list:
    """Активні HeroBanner; якщо порожньо — один слайд з SiteSettings.hero_*."""
    banners = list(HeroBanner.objects.filter(is_active=True).order_by("sort_order", "pk"))
    lang = (get_language() or "uk").split("-")[0]
    if banners:
        for banner in banners:
            url = (banner.button_url or "").strip()
            if url.startswith("/") and not url.startswith("//"):
                banner.button_url = localize_path(url, lang)
        return banners
    site = SiteSettings.load()
    eyebrow = " ".join(p for p in (site.site_name, site.tagline) if p).strip()
    return [
        SimpleNamespace(
            eyebrow=eyebrow,
            title=site.hero_title or "",
            subtitle=site.hero_subtitle or "",
            button_text="",
            button_url="",
            image=site.hero_image,
            background_image=None,
            overlay_color="#EFE9E1",
            overlay_opacity=72,
            overlay_blur=10,
            overlay_opacity_css="0.72",
            overlay_blur_css="10px",
            overlay_rgba="rgba(239, 233, 225, 0.72)",
        )
    ]


def home(request):
    sections = selectors.home_sections()
    context = {
        "categories": sections["categories"],
        "promo_collections": sections.get("promo_collections", []),
        "collection_product_sections": sections.get("collection_product_sections", []),
        "trust_badges": TrustBadge.objects.filter(is_active=True).order_by("sort_order", "pk"),
        "hero_banners": _hero_banners_for_home(),
    }
    return render(request, "catalog/home.html", context)


def catalog_list(request, category_slug=None, brand_slug=None):
    category = None
    brand = None
    if category_slug:
        children_qs = Category.objects.filter(is_active=True).order_by("sort_order", "name")
        category = get_object_or_404(
            Category.objects.select_related("parent").prefetch_related(
                Prefetch("children", queryset=children_qs)
            ),
            slug=category_slug,
            is_active=True,
        )
    if brand_slug:
        brand = get_object_or_404(Brand, slug=brand_slug, is_active=True)

    filters = selectors.parse_catalog_filters(request)
    if brand is not None:
        filters["brand_slugs"] = [brand.slug]

    qs = selectors.filter_products(
        selectors.visible_products(),
        category=category,
        brand_slugs=filters["brand_slugs"] or None,
        category_slugs=filters["category_slugs"] or None,
        attr_filters=filters["attr_filters"] or None,
        volume_slugs=filters["volume_slugs"] or None,
        stock_only=filters["stock_only"],
        sale_only=filters["sale_only"],
        query=filters["query"] or None,
        price_min=filters["price_min"],
        price_max=filters["price_max"],
    )
    sort = request.GET.get("sort", "popular")
    qs = selectors.apply_sort(qs, sort)

    paginator = Paginator(qs, 24)
    page_obj = paginator.get_page(request.GET.get("page"))

    base_query = request.GET.copy()
    base_query.pop("page", None)

    selected_attrs = {key: set(vals) for key, vals in filters["attr_filters"].items()}
    filter_groups = selectors.filter_groups_for_catalog()
    for group in filter_groups:
        group["selected_slugs"] = selected_attrs.get(group["attribute"].code, set())

    crumbs = [(_("Головна"), reverse("catalog:home"))]
    if category or brand or filters["query"]:
        crumbs.append((_("Каталог"), reverse("catalog:catalog")))
    if category:
        crumbs.append((category.name, category.get_absolute_url()))
    elif brand:
        crumbs.append((brand.name, brand.get_absolute_url()))
    elif filters["query"]:
        crumbs.append((_("Пошук"), request.path))
    else:
        crumbs.append((_("Каталог"), reverse("catalog:catalog")))

    context = {
        "base_query_string": base_query.urlencode(),
        "category": category,
        "brand": brand,
        "seo_breadcrumbs": crumbs,
        "products": page_obj,
        "page_obj": page_obj,
        "sort": sort,
        "sort_options": selectors.SORT_OPTIONS,
        "top_categories": selectors.top_level_categories(),
        "brands": selectors.active_brands(),
        "filter_groups": filter_groups,
        "volume_options": selectors.volume_options_for_catalog(),
        "selected_brands": set(filters["brand_slugs"]),
        "selected_categories": set(filters["category_slugs"]),
        "selected_volumes": set(filters["volume_slugs"]),
        "stock_only": filters["stock_only"],
        "sale_only": filters["sale_only"],
        "query": filters["query"],
        "price_min": filters["price_min"] or "",
        "price_max": filters["price_max"] or "",
        "total_count": paginator.count,
        "filters_reset_url": selectors.filters_reset_url(request.path, filters["query"]),
    }
    return render(request, "catalog/product_list.html", context)


def brand_list(request):
    context = {
        "brands": selectors.active_brands(),
        "seo_breadcrumbs": [
            (_("Головна"), reverse("catalog:home")),
            (_("Бренди"), reverse("catalog:brand_list")),
        ],
    }
    return render(request, "catalog/brand_list.html", context)


def collection_detail(request, slug):
    collection = selectors.collection_by_slug(slug)
    if collection is None:
        from django.http import Http404
        raise Http404
    qs = selectors.products_for_collection(collection)
    sort = request.GET.get("sort", "popular")
    qs = selectors.apply_sort(qs, sort)
    paginator = Paginator(qs, 24)
    page_obj = paginator.get_page(request.GET.get("page"))
    context = {
        "collection": collection,
        "products": page_obj,
        "page_obj": page_obj,
        "sort": sort,
        "sort_options": selectors.SORT_OPTIONS,
        "total_count": paginator.count,
        "base_query_string": "",
        "seo_breadcrumbs": [
            (_("Головна"), reverse("catalog:home")),
            (_("Каталог"), reverse("catalog:catalog")),
            (collection.name, collection.get_absolute_url()),
        ],
    }
    return render(request, "catalog/collection_detail.html", context)


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.select_related("brand", "category").prefetch_related(
            "images", "variants", "reviews__images",
            Prefetch(
                "product_attribute_values",
                queryset=ProductAttributeValue.objects.select_related(
                    "attribute_value__attribute",
                ).order_by(
                    "attribute_value__attribute__sort_order",
                    "attribute_value__sort_order",
                ),
            ),
        ),
        slug=slug, is_active=True,
    )
    variants = list(product.variants.filter(is_active=True))

    selected_id = request.GET.get("variant")
    current_variant = None
    if selected_id and selected_id.isdigit():
        current_variant = next((v for v in variants if v.pk == int(selected_id)), None)
    if current_variant is None:
        current_variant = product.default_variant or (variants[0] if variants else None)

    reviews_ctx = _paginate_reviews(request, product)
    related = selectors.related_products(product)
    together = selectors.bought_together(product)

    context = {
        "product": product,
        "variants": variants,
        "current_variant": current_variant,
        **reviews_ctx,
        "related_products": related,
        "bought_together_products": together,
        "review_form": ReviewForm(is_authenticated=request.user.is_authenticated),
        "pdp_attrs": selectors.pdp_attribute_groups(product),
        "seo_breadcrumbs": [
            (_("Головна"), reverse("catalog:home")),
            (product.category.name, product.category.get_absolute_url()),
            (product.name, product.get_absolute_url()),
        ],
    }
    if current_variant:
        context["dl_events_json"] = analytics.events_json(analytics.build_event(
            "view_item",
            value=current_variant.current_price,
            items=[analytics.make_item(
                item_id=current_variant.sku, item_name=product.name,
                price=current_variant.current_price,
                brand=product.brand.name, category=product.category.name,
            )],
        ))
    return render(request, "catalog/product_detail.html", context)


@require_POST
def review_create(request, slug):
    product = get_object_or_404(
        Product.objects.select_related("brand", "category").prefetch_related(
            "images", "variants", "reviews__images",
        ),
        slug=slug, is_active=True,
    )
    form = ReviewForm(request.POST, request.FILES, is_authenticated=request.user.is_authenticated)

    if form.is_valid():
        review_services.create_review(
            product=product,
            user=request.user,
            author_name=form.cleaned_data["author_name"].strip(),
            rating=int(form.cleaned_data["rating"]),
            text=form.cleaned_data["text"].strip(),
            photos=form.cleaned_data["photos"],
        )
        messages.success(request, _("Дякуємо за відгук! Він з'явиться на сторінці після модерації."))
        return redirect(f"{product.get_absolute_url()}#reviews")

    variants = list(product.variants.filter(is_active=True))
    context = {
        "product": product,
        "variants": variants,
        "current_variant": product.default_variant or (variants[0] if variants else None),
        **_paginate_reviews(request, product),
        "related_products": selectors.related_products(product),
        "bought_together_products": selectors.bought_together(product),
        "review_form": form,
        "seo_breadcrumbs": [
            (_("Головна"), reverse("catalog:home")),
            (product.category.name, product.category.get_absolute_url()),
            (product.name, product.get_absolute_url()),
        ],
    }
    return render(request, "catalog/product_detail.html", context)


@require_GET
def search_suggest(request):
    """JSON-підказки для інпута пошуку в хедері."""
    query = request.GET.get("q", "").strip()
    products = selectors.search_suggest(query)
    return JsonResponse({
        "results": [
            {
                "name": product.name,
                "brand": product.brand.name if product.brand_id else "",
                "url": product.get_absolute_url(),
            }
            for product in products
        ],
    })
