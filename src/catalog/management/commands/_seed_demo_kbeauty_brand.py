"""Демо-товари бренду K-Beauty (окремо від категорії-напряму k-beauty)."""
from decimal import Decimal

KBEAUTY_BRAND_PRODUCTS = [
    {
        "slug": "k-beauty-green-tea-toner-150-ml",
        "name": "Тонер із зеленим чаєм K-Beauty Green Tea Balancing Toner",
        "brand": "k-beauty",
        "category": "ochyshchennya",
        "short_description": (
            "Легкий тонер для щоденного відновлення pH після очищення. "
            "Підходить для комбінованої та чутливої шкіри."
        ),
        "description": (
            "Демо-картка бренду K-Beauty: зволоження без липкості, м’яке "
            "заспокоєння після вмивання."
        ),
        "usage_instructions": (
            "Після очищення нанести на ватний диск або долоні й розподілити "
            "по обличчю. Не змивати."
        ),
        "actives": "Camellia Sinensis Leaf Extract, пантенол, гіалуронова кислота",
        "inci": "Aqua, Glycerin, Butylene Glycol, Camellia Sinensis Leaf Extract…",
        "is_hit": True,
        "is_new": True,
        "image": "centella-serum.png",
        "additional": ["k-beauty"],
        "variants": [
            {
                "sku": "KB-TNR-150",
                "barcode": "4820999000101",
                "volume": "150 мл",
                "cost_price": Decimal("310.00"),
                "retail_price": Decimal("590.00"),
                "sale_price": None,
                "stock_quantity": 18,
            },
        ],
    },
    {
        "slug": "k-beauty-rice-sleeping-mask-80-ml",
        "name": "Нічна маска з рисом K-Beauty Rice Sleeping Mask",
        "brand": "k-beauty",
        "category": "masky",
        "short_description": (
            "Нічний догляд для сяяння та зволоження. Нанести товстим шаром "
            "перед сном."
        ),
        "description": (
            "Кремове текстура з рисовим екстрактом. Демо-товар для вітрини бренду."
        ),
        "usage_instructions": (
            "Увечері після сироватки нанести рівномірний шар. Змити вранці "
            "або залишити до повного вбирання."
        ),
        "actives": "Oryza Sativa Extract, ніацинамід, цераміди",
        "inci": "Aqua, Caprylic/Capric Triglyceride, Glycerin, Oryza Sativa Extract…",
        "is_hit": False,
        "is_new": True,
        "image": "pdrn-cream.png",
        "additional": ["k-beauty"],
        "variants": [
            {
                "sku": "KB-MSK-80",
                "barcode": "4820999000102",
                "volume": "80 мл",
                "cost_price": Decimal("380.00"),
                "retail_price": Decimal("720.00"),
                "sale_price": Decimal("649.00"),
                "stock_quantity": 14,
            },
        ],
    },
    {
        "slug": "k-beauty-ceramide-ampoule-30-ml",
        "name": "Ампула з церамідами K-Beauty Barrier Ampoule",
        "brand": "k-beauty",
        "category": "syrovatky-ampuly",
        "short_description": (
            "Концентрована ампула для зміцнення бар’єру шкіри та зменшення "
            "відчуття стягнутості."
        ),
        "description": (
            "Легка гелева текстура. Демо SKU бренду K-Beauty для фільтрів і PDP."
        ),
        "usage_instructions": (
            "2–3 краплі на очищену шкіру вранці та ввечері перед кремом."
        ),
        "actives": "Ceramide NP, пантенол, Madecassoside",
        "inci": "Aqua, Propanediol, Glycerin, Ceramide NP, Panthenol…",
        "is_hit": False,
        "is_new": False,
        "image": "sunscreen.png",
        "additional": ["k-beauty"],
        "variants": [
            {
                "sku": "KB-AMP-30",
                "barcode": "4820999000103",
                "volume": "30 мл",
                "cost_price": Decimal("450.00"),
                "retail_price": Decimal("890.00"),
                "sale_price": None,
                "stock_quantity": 22,
            },
        ],
    },
]
