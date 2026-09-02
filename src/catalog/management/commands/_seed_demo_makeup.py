"""Тестова декоративка з кількома відтінками на одній картці (PDP variant picker)."""
from decimal import Decimal

MAKEUP_PRODUCTS = [
    {
        "slug": "whocares-velvet-lip-color",
        "name": "Оксамитова помада whocares Velvet Lip Color",
        "brand": "whocares",
        "category": "pomady",
        "short_description": (
            "Кремове покриття з напівматовим фінішем. Чотири відтінки — окремі SKU."
        ),
        "description": (
            "Демо-картка для перевірки вибору кольору на PDP. Один товар, кілька "
            "варіантів з власним артикулом і залишком."
        ),
        "usage_instructions": "Нанести на губи з центру. За бажанням нашарувати.",
        "actives": "вітамін E, олія жожоба",
        "inci": "Ricinus Communis Seed Oil, Cera Alba, Bis-Diglyceryl Polyacyladipate-2…",
        "is_hit": False,
        "is_new": True,
        "image": "bb-cushion.png",
        "additional": [],
        "variants": [
            {
                "sku": "WC-LIP-NUDE",
                "barcode": "4820268261101",
                "shade": "Nude Rose",
                "shade_hex": "#C9898F",
                "volume": "3.5 г",
                "cost_price": Decimal("420.00"),
                "retail_price": Decimal("690.00"),
                "sale_price": None,
                "stock_quantity": 12,
            },
            {
                "sku": "WC-LIP-BRICK",
                "barcode": "4820268261102",
                "shade": "Warm Brick",
                "shade_hex": "#B5523A",
                "volume": "3.5 г",
                "cost_price": Decimal("420.00"),
                "retail_price": Decimal("690.00"),
                "sale_price": Decimal("590.00"),
                "stock_quantity": 7,
            },
            {
                "sku": "WC-LIP-BERRY",
                "barcode": "4820268261103",
                "shade": "Soft Berry",
                "shade_hex": "#8B3A4A",
                "volume": "3.5 г",
                "cost_price": Decimal("420.00"),
                "retail_price": Decimal("690.00"),
                "sale_price": None,
                "stock_quantity": 0,
            },
            {
                "sku": "WC-LIP-CORAL",
                "barcode": "4820268261104",
                "shade": "Coral Glow",
                "shade_hex": "#E07A6A",
                "volume": "3.5 г",
                "cost_price": Decimal("420.00"),
                "retail_price": Decimal("690.00"),
                "sale_price": None,
                "stock_quantity": 9,
            },
        ],
    },
    {
        "slug": "purito-soft-touch-blush",
        "name": "Рум'яна Purito Seoul Soft Touch Blush",
        "brand": "purito-seoul",
        "category": "rumyana",
        "short_description": (
            "Шовковисті рум'яна з природним світінням. Три кольори на одній картці."
        ),
        "description": (
            "Тестовий товар декоративки: вибір кольору змінює SKU, ціну не змінює."
        ),
        "usage_instructions": (
            "Нанести пензлем на яблука щік і розтушувати до скронь."
        ),
        "actives": "ніацинамід, токоферол",
        "inci": "Talc, Mica, Magnesium Stearate, Dimethicone, Niacinamide, Tocopherol…",
        "is_hit": False,
        "is_new": True,
        "image": "bb-cushion.png",
        "variants": [
            {
                "sku": "PRT-BLUSH-PINK",
                "barcode": "8809563104101",
                "shade": "Petal Pink",
                "shade_hex": "#E8A4B0",
                "volume": "4 г",
                "cost_price": Decimal("380.00"),
                "retail_price": Decimal("620.00"),
                "sale_price": None,
                "stock_quantity": 11,
            },
            {
                "sku": "PRT-BLUSH-PEACH",
                "barcode": "8809563104102",
                "shade": "Warm Peach",
                "shade_hex": "#E8A07A",
                "volume": "4 г",
                "cost_price": Decimal("380.00"),
                "retail_price": Decimal("620.00"),
                "sale_price": None,
                "stock_quantity": 6,
            },
            {
                "sku": "PRT-BLUSH-ROSE",
                "barcode": "8809563104103",
                "shade": "Dusty Rose",
                "shade_hex": "#C47A86",
                "volume": "4 г",
                "cost_price": Decimal("380.00"),
                "retail_price": Decimal("620.00"),
                "sale_price": None,
                "stock_quantity": 4,
            },
        ],
    },
]
