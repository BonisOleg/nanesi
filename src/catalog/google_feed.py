"""Живий XML-фід Google Merchant: один рядок = один ProductVariant."""
from decimal import Decimal
from xml.sax.saxutils import escape

from django.conf import settings
from django.http import HttpResponse
from django.utils import translation
from django.utils.html import strip_tags

from src.catalog.models import Category, ProductVariant
from src.content.models import SiteSettings

GOOGLE_CATEGORY_BY_ROOT_SLUG = {
    "doglyad-za-oblychchyam": "567",
    "soncezahyst-spf": "2844",
    "makiyazh": "477",
    "doglyad-za-tilom": "474",
    "doglyad-za-volossyam": "486",
    "nabory-ta-miniatyury": "6069",
    "k-beauty": "473",
}
DEFAULT_GOOGLE_CATEGORY = "473"
UMBRELLA_SLUGS = frozenset({"all-types", "all-ages"})
MONEY_QUANT = Decimal("0.01")


def _translated(obj, field: str) -> str:
    for attr in (field, f"{field}_uk", f"{field}_en", f"{field}_ru"):
        value = getattr(obj, attr, None)
        if value:
            return str(value).strip()
    return ""


def _cdata(text: str) -> str:
    safe = (text or "").replace("]]>", "]]]]><![CDATA[>")
    return f"<![CDATA[{safe}]]>"


def _money(value) -> str:
    amount = Decimal(value).quantize(MONEY_QUANT)
    return f"{amount:.2f} UAH"


def _get_active_variants():
    return (
        ProductVariant.objects.filter(
            is_active=True,
            feed_exclude=False,
            product__is_active=True,
        )
        .select_related("product", "product__brand", "product__category")
        .prefetch_related("product__images", "product__attribute_values__attribute")
        .order_by("product_id", "sort_order", "pk")
    )


def _root_and_path(category, by_id: dict) -> tuple[object | None, str]:
    chain = []
    current = category
    seen = set()
    while current and current.pk not in seen:
        seen.add(current.pk)
        chain.append(current)
        current = by_id.get(current.parent_id) if current.parent_id else None
    chain.reverse()
    root = chain[0] if chain else None
    path = " > ".join(["Головна", "Каталог", *[_translated(item, "name") for item in chain]])
    return root, path


def _main_image_url(product, request) -> str:
    images = list(product.images.all())
    chosen = next((img for img in images if img.is_main and img.image), None)
    if chosen is None:
        chosen = next((img for img in images if img.image), None)
    if chosen is None:
        return ""
    return request.build_absolute_uri(chosen.image.url)


def _attr_values(product, code: str) -> list[str]:
    values = []
    for attr_value in product.attribute_values.all():
        if attr_value.attribute.code != code:
            continue
        if attr_value.is_umbrella or attr_value.slug in UMBRELLA_SLUGS:
            continue
        label = _translated(attr_value, "value")
        if label:
            values.append(label)
    return values


def _badge(product, variant) -> str:
    if product.is_new:
        return "Новинка"
    if product.is_hit:
        return "Хіт"
    if variant.sale_price is not None:
        return "Акція"
    return ""


def _title(variant) -> str:
    extra = " ".join(filter(None, [variant.shade, variant.volume]))
    name = _translated(variant.product, "name")
    return f"{name} {extra}".strip() if extra else name


def _description(product) -> str:
    raw = (
        _translated(product, "description")
        or _translated(product, "short_description")
        or _translated(product, "name")
    )
    return strip_tags(raw).strip()


def _item_xml(variant, request, categories_by_id: dict) -> str:
    product = variant.product
    root, product_type = _root_and_path(product.category, categories_by_id)
    root_slug = getattr(root, "slug", "") if root else ""
    google_cat = GOOGLE_CATEGORY_BY_ROOT_SLUG.get(root_slug, DEFAULT_GOOGLE_CATEGORY)
    label_0 = _translated(root, "name") if root else ""
    label_2 = (
        _translated(product.category, "name") if product.category_id else ""
    ) or ", ".join(_attr_values(product, "concern"))
    label_3 = ", ".join(_attr_values(product, "skin_type"))
    link = request.build_absolute_uri(f"{product.get_absolute_url()}?variant={variant.pk}")
    image = _main_image_url(product, request)
    availability = "in stock" if variant.in_stock else "out of stock"
    barcode = (variant.barcode or "").strip()
    ident = (
        f"<g:gtin>{escape(barcode)}</g:gtin>"
        if barcode
        else "<g:identifier_exists>no</g:identifier_exists>"
    )
    sale_xml = ""
    if variant.sale_price is not None:
        sale_xml = f"<g:sale_price>{_money(variant.sale_price)}</g:sale_price>"
    return (
        "<item>"
        f"<g:id>{escape(variant.sku)}</g:id>"
        f"<g:title>{_cdata(_title(variant))}</g:title>"
        f"<g:description>{_cdata(_description(product))}</g:description>"
        f"<g:link>{escape(link)}</g:link>"
        f"<g:image_link>{escape(image)}</g:image_link>"
        f"<g:availability>{availability}</g:availability>"
        f"<g:price>{_money(variant.retail_price)}</g:price>"
        f"{sale_xml}"
        "<g:condition>new</g:condition>"
        f"<g:brand>{_cdata(_translated(product.brand, 'name') if product.brand_id else '')}</g:brand>"
        f"{ident}"
        f"<g:google_product_category>{google_cat}</g:google_product_category>"
        f"<g:product_type>{_cdata(product_type)}</g:product_type>"
        f"<g:custom_label_0>{_cdata(label_0)}</g:custom_label_0>"
        f"<g:custom_label_1>{_cdata(_badge(product, variant))}</g:custom_label_1>"
        f"<g:custom_label_2>{_cdata(label_2)}</g:custom_label_2>"
        f"<g:custom_label_3>{_cdata(label_3)}</g:custom_label_3>"
        "</item>"
    )


def google_merchant_feed(request):
    with translation.override(settings.LANGUAGE_CODE):
        return _render_google_merchant_feed(request)


def _render_google_merchant_feed(request):
    site = SiteSettings.load()
    site_url = request.build_absolute_uri("/")
    categories_by_id = {cat.pk: cat for cat in Category.objects.all()}
    items = [
        _item_xml(variant, request, categories_by_id)
        for variant in _get_active_variants()
    ]
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<rss version="2.0" xmlns:g="http://base.google.com/ns/1.0">'
        "<channel>"
        f"<title>{_cdata(site.site_name or 'Products')}</title>"
        f"<link>{escape(site_url)}</link>"
        "<description>Google Merchant product feed</description>"
        + "".join(items)
        + "</channel></rss>"
    )
    return HttpResponse(xml, content_type="application/xml; charset=utf-8")
