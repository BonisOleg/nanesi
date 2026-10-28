"""Фасад: `from src.catalog.models import X` продовжує працювати після розбиття файлу
(ecommerce_db_schema_skill, крок 8 — файл моделей app'у >500 рядків розбито з фасадом)."""
from src.catalog.models_1 import (
    Brand,
    Category,
    CategoryProductPosition,
    Product,
    ProductCrossSell,
    ProductImage,
    ProductVariant,
    Supplier,
)
from src.catalog.models_2 import (
    Attribute,
    AttributeValue,
    Collection,
    CollectionProduct,
    ProductAttributeValue,
    Review,
    ReviewImage,
)

__all__ = [
    "Category",
    "CategoryProductPosition",
    "Brand",
    "Supplier",
    "Product",
    "ProductCrossSell",
    "ProductVariant",
    "ProductImage",
    "Attribute",
    "AttributeValue",
    "ProductAttributeValue",
    "Collection",
    "CollectionProduct",
    "Review",
    "ReviewImage",
]
