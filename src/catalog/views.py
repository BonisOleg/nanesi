from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from src.catalog import selectors
from src.catalog.forms import ReviewForm
from src.catalog.models import Brand, Category, Product
from src.catalog.services import reviews as review_services
from src.content.models import TrustBadge
from src.core import analytics


def home(request):
    sections = selectors.home_sections()
    context = {
        "categories": sections["categories"],
        "hits_and_new": sections["hits_and_new"],
        "trust_badges": TrustBadge.objects.filter(is_active=True),
    }
    return render(request, "catalog/home.html", context)


def _parse_filters(request):
    return {
        "brand_slugs": request.GET.getlist("brand"),
        "category_slugs": request.GET.getlist("category"),
        "attribute_value_ids": [v for v in request.GET.getlist("attr") if v.isdigit()],
        "stock_only": ("stock" in request.GET) if request.GET else True,
        "sale_only": request.GET.get("sale") == "1",
        "query": request.GET.get("q", "").strip(),
    }


def catalog_list(request, category_slug=None, brand_slug=None):
    category = None
    brand = None
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug, is_active=True)
    if brand_slug:
        brand = get_object_or_404(Brand, slug=brand_slug, is_active=True)

    filters = _parse_filters(request)
    if brand is not None:
        filters["brand_slugs"] = [brand.slug]

    qs = selectors.filter_products(
        selectors.visible_products(),
        category=category,
        brand_slugs=filters["brand_slugs"] or None,
        category_slugs=filters["category_slugs"] or None,
        attribute_value_ids=filters["attribute_value_ids"] or None,
        stock_only=filters["stock_only"],
        sale_only=filters["sale_only"],
        query=filters["query"] or None,
    )
    sort = request.GET.get("sort", "popular")
    qs = selectors.apply_sort(qs, sort)

    paginator = Paginator(qs, 24)
    page_obj = paginator.get_page(request.GET.get("page"))

    base_query = request.GET.copy()
    base_query.pop("page", None)

    context = {
        "base_query_string": base_query.urlencode(),
        "category": category,
        "brand": brand,
        "products": page_obj,
        "page_obj": page_obj,
        "sort": sort,
        "sort_options": selectors.SORT_OPTIONS,
        "top_categories": selectors.top_level_categories(),
        "brands": selectors.active_brands(),
        "attributes": selectors.filterable_attributes(),
        "selected_brands": set(filters["brand_slugs"]),
        "selected_categories": set(filters["category_slugs"]),
        "selected_attr_values": {int(v) for v in filters["attribute_value_ids"]},
        "stock_only": filters["stock_only"],
        "sale_only": filters["sale_only"],
        "query": filters["query"],
        "total_count": paginator.count,
    }
    return render(request, "catalog/product_list.html", context)


def brand_list(request):
    context = {"brands": selectors.active_brands()}
    return render(request, "catalog/brand_list.html", context)


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.select_related("brand", "category").prefetch_related(
            "images", "variants", "reviews__images",
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

    reviews = product.reviews.filter(is_approved=True).order_by("-created_at")
    reviews_count = reviews.count()
    rating_avg = (
        sum(r.rating for r in reviews) / reviews_count if reviews_count else None
    )
    related = selectors.related_products(product)

    context = {
        "product": product,
        "variants": variants,
        "current_variant": current_variant,
        "reviews": reviews,
        "reviews_count": reviews_count,
        "rating_avg": rating_avg,
        "related_products": related,
        "review_form": ReviewForm(is_authenticated=request.user.is_authenticated),
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
    reviews = product.reviews.filter(is_approved=True).order_by("-created_at")
    reviews_count = reviews.count()
    context = {
        "product": product,
        "variants": variants,
        "current_variant": product.default_variant or (variants[0] if variants else None),
        "reviews": reviews,
        "reviews_count": reviews_count,
        "rating_avg": sum(r.rating for r in reviews) / reviews_count if reviews_count else None,
        "related_products": selectors.related_products(product),
        "review_form": form,
    }
    return render(request, "catalog/product_detail.html", context)
