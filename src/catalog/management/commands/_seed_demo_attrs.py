"""Фасети каталогу для seed_demo: групи Attribute + значення + прив’язка до товарів."""

ATTRIBUTE_GROUPS = [
    {"code": "skin_type", "name": "Тип шкіри", "sort": 10, "show_on_pdp": True},
    {"code": "concern", "name": "Проблема / призначення", "sort": 20, "show_on_pdp": True},
    {"code": "country", "name": "Країна / напрям", "sort": 30, "show_on_pdp": True},
    {"code": "ingredient", "name": "Інгредієнти", "sort": 40, "show_on_pdp": True},
    {"code": "age", "name": "Вік", "sort": 50, "show_on_pdp": True},
    {"code": "spf", "name": "SPF", "sort": 60, "show_on_pdp": True},
]

UMBRELLA_VALUE_SLUGS = frozenset({"all-types", "all-ages"})

ATTRIBUTE_VALUES = {
    "skin_type": [
        ("all-types", "Усі типи"),
        ("sensitive", "Чутлива"),
        ("dry", "Суха"),
        ("normal", "Нормальна"),
        ("combination", "Комбінована"),
        ("oily", "Жирна"),
    ],
    "concern": [
        ("dehydration", "Зневоднення"),
        ("dryness", "Сухість"),
        ("barrier", "Ослаблений бар’єр"),
        ("wrinkles", "Дрібні зморшки"),
        ("sensitivity", "Чутливість"),
        ("redness", "Почервоніння"),
        ("uv-protection", "Захист від UV"),
        ("photoaging", "Фотостаріння"),
        ("tone", "Вирівнювання тону"),
        ("scalp-balance", "Баланс шкіри голови"),
    ],
    "country": [
        ("south-korea", "Південна Корея"),
        ("ukraine", "Україна"),
    ],
    "ingredient": [
        ("niacinamide", "Ніацинамід"),
        ("ceramides", "Цераміди"),
        ("centella", "Центелла"),
        ("panthenol", "Пантенол"),
        ("hyaluronic-acid", "Гіалуронова кислота"),
        ("peptides", "Пептиди"),
        ("pdrn", "PDRN"),
        ("wheat-protein", "Протеїн пшениці"),
    ],
    "age": [
        ("all-ages", "Усі віки"),
        ("25-plus", "25+"),
        ("35-plus", "35+"),
    ],
    "spf": [
        ("spf30", "SPF30"),
        ("spf50-plus", "SPF50+"),
    ],
}

# product.slug → { attribute.code: [value.slug, ...] }
PRODUCT_ATTRIBUTES = {
    "whocares-vegan-pdrn-cream-50-ml": {
        "skin_type": ["all-types", "sensitive"],
        "concern": ["dehydration", "dryness", "barrier", "wrinkles"],
        "country": ["south-korea"],
        "ingredient": ["niacinamide", "ceramides", "peptides", "pdrn"],
        "age": ["35-plus", "all-ages"],
    },
    "purito-wonder-releaf-centella-serum-60-ml": {
        "skin_type": ["sensitive", "all-types"],
        "concern": ["sensitivity", "redness", "dehydration", "barrier"],
        "country": ["south-korea"],
        "ingredient": ["centella", "niacinamide", "panthenol", "hyaluronic-acid", "peptides", "ceramides"],
        "age": ["all-ages"],
    },
    "purito-daily-soft-touch-sunscreen-spf50": {
        "skin_type": ["all-types", "sensitive"],
        "concern": ["uv-protection", "photoaging", "dehydration"],
        "country": ["south-korea"],
        "ingredient": ["ceramides", "centella", "panthenol"],
        "age": ["all-ages"],
        "spf": ["spf50-plus"],
    },
    "whocares-balancing-shampoo-300-ml": {
        "skin_type": ["dry", "normal"],
        "concern": ["dryness", "scalp-balance"],
        "country": ["ukraine"],
        "ingredient": ["wheat-protein"],
        "age": ["all-ages"],
    },
    "purito-centella-bb-cushion-13": {
        "skin_type": ["all-types"],
        "concern": ["tone", "uv-protection"],
        "country": ["south-korea"],
        "ingredient": ["centella", "niacinamide", "ceramides", "hyaluronic-acid"],
        "age": ["all-ages"],
        "spf": ["spf30"],
    },
    "whocares-velvet-lip-color": {
        "skin_type": ["all-types"],
        "concern": ["tone"],
        "country": ["ukraine"],
        "age": ["all-ages"],
    },
    "purito-soft-touch-blush": {
        "skin_type": ["all-types"],
        "concern": ["tone"],
        "country": ["south-korea"],
        "ingredient": ["niacinamide"],
        "age": ["all-ages"],
    },
}
