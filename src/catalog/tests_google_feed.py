import tempfile
from decimal import Decimal
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import translation
from PIL import Image

from src.catalog.models import (
    Attribute,
    AttributeValue,
    Brand,
    Category,
    Product,
    ProductAttributeValue,
    ProductImage,
    ProductVariant,
)


def _tiny_png(name: str = "pdp.png") -> SimpleUploadedFile:
    buf = BytesIO()
    Image.new("RGB", (8, 8), (180, 40, 40)).save(buf, format="PNG")
    return SimpleUploadedFile(name, buf.getvalue(), content_type="image/png")


class GoogleMerchantFeedTests(TestCase):
    def setUp(self):
        translation.activate("uk")
        self.addCleanup(translation.activate, "uk")
        self._media = tempfile.TemporaryDirectory()
        self._media_override = override_settings(MEDIA_ROOT=self._media.name)
        self._media_override.enable()
        self.addCleanup(self._media_override.disable)
        self.addCleanup(self._media.cleanup)

        self.face = Category.objects.create(
            name="Догляд за обличчям", slug="doglyad-za-oblychchyam",
        )
        self.toners = Category.objects.create(
            name="Тонери", slug="tonery", parent=self.face,
        )
        self.brand = Brand.objects.create(name="SKIN1004", slug="skin1004-feed")
        self.product = Product.objects.create(
            name="Очищувальне молочко з центелою SKIN1004",
            slug="centella-milk",
            brand=self.brand,
            category=self.toners,
            description="Детальний опис товару",
            is_active=True,
            is_new=True,
            is_hit=True,
        )
        ProductImage.objects.create(product=self.product, image=_tiny_png(), is_main=True)
        self.variant = ProductVariant.objects.create(
            product=self.product,
            sku="SKIN1004_AMP_10",
            barcode="8809563100316",
            volume="200мл",
            retail_price=Decimal("920.00"),
            sale_price=Decimal("870.00"),
            stock_quantity=4,
            is_active=True,
        )
        skin = Attribute.objects.create(code="skin_type", name="Тип шкіри")
        concern = Attribute.objects.create(code="concern", name="Проблема / призначення")
        dry = AttributeValue.objects.create(attribute=skin, value="Суха", slug="dry")
        all_types = AttributeValue.objects.create(
            attribute=skin, value="Усі типи", slug="all-types", is_umbrella=True,
        )
        hydrate = AttributeValue.objects.create(
            attribute=concern, value="Інтенсивне зволоження", slug="hydrate",
        )
        ProductAttributeValue.objects.create(product=self.product, attribute_value=dry)
        ProductAttributeValue.objects.create(product=self.product, attribute_value=all_types)
        ProductAttributeValue.objects.create(product=self.product, attribute_value=hydrate)

        self.excluded = ProductVariant.objects.create(
            product=self.product,
            sku="SKIP_ME",
            retail_price=Decimal("10.00"),
            stock_quantity=1,
            is_active=True,
            feed_exclude=True,
        )

        makeup_root = Category.objects.create(name="Макіяж", slug="makiyazh")
        makeup_product = Product.objects.create(
            name="Тінт", slug="tint-feed", brand=self.brand, category=makeup_root, is_active=True,
        )
        self.no_gtin = ProductVariant.objects.create(
            product=makeup_product,
            sku="TINT_NO_GTIN",
            retail_price=Decimal("450.00"),
            stock_quantity=0,
            is_active=True,
        )

    def test_feed_xml_contract(self):
        response = self.client.get("/feeds/google.xml")
        self.assertEqual(response.status_code, 200)
        self.assertIn("application/xml", response["Content-Type"])
        xml = response.content.decode("utf-8")
        self.assertIn("<g:id>SKIN1004_AMP_10</g:id>", xml)
        self.assertIn("<g:price>920.00 UAH</g:price>", xml)
        self.assertIn("<g:sale_price>870.00 UAH</g:sale_price>", xml)
        self.assertIn("<g:gtin>8809563100316</g:gtin>", xml)
        self.assertIn("<g:availability>in stock</g:availability>", xml)
        self.assertIn("<g:google_product_category>567</g:google_product_category>", xml)
        self.assertIn("<g:custom_label_0><![CDATA[Догляд за обличчям]]></g:custom_label_0>", xml)
        self.assertIn("<g:custom_label_1><![CDATA[Новинка]]></g:custom_label_1>", xml)
        self.assertIn("<g:custom_label_2><![CDATA[Тонери]]></g:custom_label_2>", xml)
        self.assertIn("<g:custom_label_3><![CDATA[Суха]]></g:custom_label_3>", xml)
        self.assertIn("Головна > Каталог > Догляд за обличчям > Тонери", xml)
        self.assertIn("?variant=", xml)
        self.assertNotIn("SKIP_ME", xml)
        self.assertIn("<g:id>TINT_NO_GTIN</g:id>", xml)
        self.assertIn("<g:identifier_exists>no</g:identifier_exists>", xml)
        self.assertIn("<g:availability>out of stock</g:availability>", xml)
        self.assertIn("<g:google_product_category>477</g:google_product_category>", xml)
        self.assertNotIn("Усі типи", xml)
