"""Дані для seed_demo: тестові SKU з «Відповідь клієнта — тестові товари.md» + мокап."""
from decimal import Decimal

STATIC_PAGES = [
    {
        "slug": "pro-nas",
        "title": "Про нас",
        "body": (
            "<p>NANESI — мультибрендовий beauty store. Ми підбираємо формули з "
            "прозорими складами та зручною доставкою по Україні.</p>"
            "<p>Контент сторінки можна замінити в адмінці.</p>"
        ),
    },
    {
        "slug": "dostavka-i-oplata",
        "title": "Доставка і оплата",
        "body": (
            "<p>Доставка Новою Поштою та Укрпоштою. Безкоштовна доставка — "
            "від суми, яку виставляєте в Налаштуваннях сайту.</p>"
            "<p>Оплата: післяплата, банківський переказ; онлайн-оплата — після "
            "підключення LiqPay.</p>"
            "<p>Обмін та повернення: зверніться до служби підтримки протягом "
            "14 днів (умови уточнюються Замовником).</p>"
        ),
    },
    {
        "slug": "oferta",
        "title": "Публічна оферта",
        "body": (
            "<p>Текст публічної оферти. Замініть на юридичний документ "
            "Замовника в адмінці.</p>"
        ),
    },
    {
        "slug": "polityka-konfidentsiinosti",
        "title": "Політика конфіденційності",
        "body": (
            "<p>Ми обробляємо персональні дані лише для виконання замовлень "
            "і зворотного зв’язку. Повний текст політики — від Замовника.</p>"
        ),
    },
]

# parent_slug=None → корінь; children — вкладені
CATEGORIES = [
    {"slug": "doglyad-za-oblychchyam", "name": "Догляд за обличчям", "parent": None, "sort": 10},
    {"slug": "kremy-dlya-oblychchya", "name": "Креми для обличчя", "parent": "doglyad-za-oblychchyam", "sort": 11},
    {"slug": "syrovatky-ampuly", "name": "Сироватки / ампули", "parent": "doglyad-za-oblychchyam", "sort": 12},
    {"slug": "soncezahyst-spf", "name": "Сонцезахист SPF", "parent": None, "sort": 20},
    {"slug": "spf-dlya-oblychchya", "name": "Для обличчя", "parent": "soncezahyst-spf", "sort": 21},
    {"slug": "doglyad-za-volossyam", "name": "Догляд за волоссям", "parent": None, "sort": 30},
    {"slug": "shampuni", "name": "Шампуні", "parent": "doglyad-za-volossyam", "sort": 31},
    {"slug": "makiyazh", "name": "Макіяж", "parent": None, "sort": 40},
    {"slug": "tonalni-kushony", "name": "Тональні засоби / Кушони", "parent": "makiyazh", "sort": 41},
]

BRANDS = [
    {"slug": "whocares", "name": "whocares"},
    {"slug": "purito-seoul", "name": "Purito Seoul"},
]

SUPPLIER_NAME = "Cosmetics Factory"

PRODUCTS = [
    {
        "slug": "whocares-vegan-pdrn-cream-50-ml",
        "name": (
            "Зволожувальний крем для обличчя із веганськими полінуклеотидами "
            "whocares Vegan PDRN Cream 50 ml"
        ),
        "brand": "whocares",
        "category": "kremy-dlya-oblychchya",
        "short_description": (
            "Зволожувальний крем для щоденного догляду, який допомагає підтримувати "
            "захисний бар’єр шкіри, зменшувати прояви сухості та вікових змін."
        ),
        "description": (
            "Формула з рослинною альтернативою PDRN, пептидами, ніацинамідом, "
            "скваланом і церамідами сприяє зволоженню, відновленню та пружності шкіри."
        ),
        "usage_instructions": (
            "Нанести невелику кількість крему на очищену та тонізовану шкіру "
            "обличчя вранці та/або ввечері."
        ),
        "actives": (
            "10% MC-PhytoDNA Rose Complex, 2% Celyscence, 2% ніацинамід, 2% сквалан, "
            "Bifida Ferment Lysate, Pepta-5, цераміди, ектоїн"
        ),
        "inci": (
            "Aqua, Butylene Glycol, Caprylic/Capric Triglyceride, Glycerin, "
            "Cetyl Ethylhexanoate, Squalane, Niacinamide, 1,2-Hexanediol, "
            "Bifida Ferment Lysate…"
        ),
        "is_hit": False,
        "is_new": False,
        "image": "pdrn-cream.png",
        "variants": [
            {
                "sku": "000005739",
                "barcode": "4820268260246",
                "volume": "50 мл",
                "cost_price": Decimal("620.00"),
                "retail_price": Decimal("1299.00"),
                "sale_price": Decimal("844.00"),
                "stock_quantity": 25,
            },
        ],
    },
    {
        "slug": "purito-wonder-releaf-centella-serum-60-ml",
        "name": (
            "Сироватка з екстрактом центелли без ароматизаторів Purito Seoul "
            "Wonder Releaf Centella Serum Unscented 60 ml"
        ),
        "brand": "purito-seoul",
        "category": "syrovatky-ampuly",
        "short_description": (
            "Заспокійлива сироватка без ароматизаторів для чутливої шкіри. "
            "Допомагає зменшувати почервоніння та дискомфорт."
        ),
        "description": (
            "Підтримує зволоження і захисний бар’єр. Розроблена насамперед "
            "для чутливої шкіри, підходить і іншим типам."
        ),
        "usage_instructions": (
            "Після очищення та тонера нанести 2–3 натискання сироватки на "
            "обличчя та шию. Легко поплескати до вбирання."
        ),
        "actives": (
            "Korean Centella Asiatica, ніацинамід, пантенол, Sodium Hyaluronate, "
            "Madecassoside, Asiaticoside, пептиди, Ceramide NP, алантоїн"
        ),
        "inci": (
            "Water, Glycerin, Dipropylene Glycol, Propanediol, "
            "Centella Asiatica Extract, Butylene Glycol, Niacinamide…"
        ),
        "is_hit": True,
        "is_new": False,
        "image": "centella-serum.png",
        "variants": [
            {
                "sku": "8809563100316",
                "barcode": "8809563100316",
                "volume": "60 мл",
                "cost_price": Decimal("681.00"),
                "retail_price": Decimal("940.00"),
                "sale_price": None,
                "stock_quantity": 30,
            },
        ],
    },
    {
        "slug": "purito-daily-soft-touch-sunscreen-spf50",
        "name": (
            "Сонцезахисний крем з керамідами Purito Seoul Daily Soft Touch "
            "Sunscreen SPF50+ PA++++ 60 ml"
        ),
        "brand": "purito-seoul",
        "category": "spf-dlya-oblychchya",
        "short_description": (
            "Легкий сонцезахисний крем широкого спектра SPF50+ PA++++ "
            "без вираженого білого сліду."
        ),
        "description": (
            "Цераміди, центелла та пантенол допомагають підтримувати "
            "зволоження та захисний бар’єр під час щоденного SPF."
        ),
        "usage_instructions": (
            "Нанести рівномірно як останній етап ранкового догляду приблизно "
            "за 15 хвилин до виходу на сонце. За необхідності поновлювати."
        ),
        "actives": (
            "5 видів церамідів, Centella Asiatica, пантенол, токоферол, "
            "бісаболол + сучасні UV-фільтри"
        ),
        "inci": (
            "Water, Propanediol, Dibutyl Adipate, Dicaprylyl Carbonate, "
            "Diethylamino Hydroxybenzoyl Hexyl Benzoate…"
        ),
        "is_hit": False,
        "is_new": True,
        "image": "sunscreen.png",
        "variants": [
            {
                "sku": "8809563102600",
                "barcode": "8809563102600",
                "volume": "60 мл",
                "cost_price": Decimal("681.00"),
                "retail_price": Decimal("940.00"),
                "sale_price": None,
                "stock_quantity": 40,
            },
        ],
    },
    {
        "slug": "whocares-balancing-shampoo-300-ml",
        "name": "Шампунь безсульфатний whocares Balancing Shampoo 300 ml",
        "brand": "whocares",
        "category": "shampuni",
        "short_description": (
            "Безсульфатний шампунь для делікатного очищення сухої "
            "та нормальної шкіри голови."
        ),
        "description": (
            "Рослинні екстракти допомагають заспокоювати шкіру, підтримувати "
            "її баланс і зміцнювати волосся без пересушування."
        ),
        "usage_instructions": (
            "Нанести на вологу шкіру голови та волосся, помасажувати та "
            "ретельно змити водою. За необхідності повторити."
        ),
        "actives": (
            "Гідролізований протеїн пшениці, розмарин, кропива, береза, "
            "хвощ, деревій, мати-й-мачуха, чебрець, екстракт кокоса"
        ),
        "inci": (
            "Aqua, Cocamidopropyl Betaine, Sodium Lauroyl Methyl Isethionate, "
            "Lauryl Glucoside, Coco-Glucoside…"
        ),
        "is_hit": False,
        "is_new": False,
        "image": "shampoo.png",
        "variants": [
            {
                "sku": "000005720",
                "barcode": "4820268260215",
                "volume": "300 мл",
                "cost_price": Decimal("649.00"),
                "retail_price": Decimal("989.00"),
                "sale_price": None,
                "stock_quantity": 20,
            },
        ],
    },
    {
        "slug": "purito-centella-bb-cushion-13",
        "name": (
            "Кушон з екстрактом центелли Purito Seoul Wonder Releaf Centella "
            "BB Cushion №13 Neutral Ivory"
        ),
        "brand": "purito-seoul",
        "category": "tonalni-kushony",
        "short_description": (
            "BB-кушон з можливістю нашаровування. Вирівнює тон і приховує "
            "недосконалості, зберігаючи природний вигляд."
        ),
        "description": (
            "Формула містить центеллу, зволожувальні компоненти та SPF30 PA+++."
        ),
        "usage_instructions": (
            "Набрати невелику кількість засобу пухівкою та нанести на обличчя "
            "легкими притискальними рухами. За необхідності нашарувати."
        ),
        "actives": (
            "Korean Centella Asiatica, Sodium Hyaluronate, цераміди, "
            "ніацинамід, токоферол, аденозин"
        ),
        "inci": (
            "Water, Titanium Dioxide, Methyl Trimethicone, "
            "Caprylic/Capric Triglyceride, Cetyl Ethylhexanoate, Zinc Oxide…"
        ),
        "is_hit": True,
        "is_new": False,
        "image": "bb-cushion.png",
        "variants": [
            {
                "sku": "8809563103355",
                "barcode": "8809563103355",
                "shade": "№13 Neutral Ivory",
                "volume": "15 г + рефіл 15 г",
                "cost_price": Decimal("978.00"),
                "retail_price": Decimal("1350.00"),
                "sale_price": None,
                "stock_quantity": 15,
            },
        ],
    },
]

SEO_LANDING = {
    "path": "k-beauty-doglyad",
    "title": "K-Beauty догляд",
    "meta_title": "K-Beauty догляд — NANESI",
    "meta_description": "Добірка корейського догляду: сироватки, SPF, креми.",
    "body": "<p>Тестова SEO-посадкова для перевірки sitemap і catch-all URL.</p>",
    "is_indexed": True,
    "is_active": True,
}

TRUST_BADGES = [
    {"icon_label": "01", "title": "Оригінали", "text": "Лише офіційні постачання", "sort_order": 1},
    {"icon_label": "02", "title": "Доставка", "text": "Нова Пошта та Укрпошта", "sort_order": 2},
    {"icon_label": "03", "title": "Підбір", "text": "Допомога з формулами", "sort_order": 3},
]
