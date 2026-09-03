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
        ),
    },
    {
        "slug": "obmin-ta-povernennya",
        "title": "Обмін та повернення",
        "body": (
            "<p>Ви можете обміняти або повернути товар належної якості протягом "
            "14 днів з моменту отримання замовлення.</p>"
            "<p>Товар має бути в оригінальній упаковці, без слідів використання, "
            "зі збереженими пломбами та ярликами (якщо передбачені).</p>"
            "<p>Для оформлення обміну чи повернення зверніться до служби підтримки "
            "із номером замовлення. Умови можуть уточнюватися Замовником в адмінці.</p>"
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
    {
        "slug": "kontakty",
        "title": "Контакти",
        "body": (
            "<p>Зв’яжіться з нами зручним способом — відповімо в робочі години.</p>"
            "<p>Актуальні телефон, email і графік також у блоці контактів нижче "
            "(керуються в налаштуваннях сайту).</p>"
        ),
    },
]

# parent_slug=None → корінь; children — вкладені.
# Порядок коренів — як у прикладі шапки: обличчя → макіяж → тіло → волосся.
# show_in_header=True — лише 4 позиції в нижній смузі (+ Бренди / Акції в шаблоні).
CATEGORIES = [
    {"slug": "doglyad-za-oblychchyam", "name": "Догляд за обличчям", "parent": None, "sort": 10, "show_in_header": True},
    {"slug": "kremy-dlya-oblychchya", "name": "Креми для обличчя", "parent": "doglyad-za-oblychchyam", "sort": 11},
    {"slug": "syrovatky-ampuly", "name": "Сироватки / ампули", "parent": "doglyad-za-oblychchyam", "sort": 12},
    {"slug": "ochyshchennya", "name": "Очищення", "parent": "doglyad-za-oblychchyam", "sort": 13},
    {"slug": "masky", "name": "Маски", "parent": "doglyad-za-oblychchyam", "sort": 14},
    {"slug": "makiyazh", "name": "Макіяж", "parent": None, "sort": 20, "show_in_header": True},
    {"slug": "tonalni-kushony", "name": "Тональні засоби / Кушони", "parent": "makiyazh", "sort": 21},
    {"slug": "pomady", "name": "Помади", "parent": "makiyazh", "sort": 22},
    {"slug": "rumyana", "name": "Рум'яна", "parent": "makiyazh", "sort": 23},
    {"slug": "doglyad-za-tilom", "name": "Догляд за тілом", "parent": None, "sort": 30, "show_in_header": True},
    {"slug": "doglyad-za-volossyam", "name": "Догляд за волоссям", "parent": None, "sort": 40, "show_in_header": True},
    {"slug": "shampuni", "name": "Шампуні", "parent": "doglyad-za-volossyam", "sort": 41},
    {"slug": "soncezahyst-spf", "name": "Сонцезахист SPF", "parent": None, "sort": 50},
    {"slug": "spf-dlya-oblychchya", "name": "Для обличчя", "parent": "soncezahyst-spf", "sort": 51},
    {"slug": "nabory-ta-miniatyury", "name": "Набори та мініатюри", "parent": None, "sort": 60},
    {"slug": "k-beauty", "name": "K-Beauty", "parent": None, "sort": 70},
]

BRANDS = [
    {"slug": "whocares", "name": "WhoCares"},
    {"slug": "purito-seoul", "name": "Purito Seoul"},
    {"slug": "k-beauty", "name": "K-Beauty"},
]

SUPPLIER_NAME = "Cosmetics Factory"

PRODUCTS = [
    {
        "slug": "whocares-vegan-pdrn-cream-50-ml",
        "name": (
            "Зволожувальний крем для обличчя із веганськими полінуклеотидами "
            "whocares Vegan PDRN Cream"
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
            "Wonder Releaf Centella Serum Unscented"
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
            "Sunscreen SPF50+ PA++++"
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
        "name": "Шампунь безсульфатний whocares Balancing Shampoo",
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
        "name": "Кушон з екстрактом центелли Purito Seoul Wonder Releaf Centella BB Cushion",
        "brand": "purito-seoul",
        "category": "tonalni-kushony",
        "short_description": (
            "BB-кушон з можливістю нашаровування. Вирівнює тон і приховує "
            "недосконалості, зберігаючи природний вигляд."
        ),
        "description": (
            "Формула містить центеллу, зволожувальні компоненти та SPF30 PA+++. "
            "Відтінки №13 / №21 / №23 — як окремі SKU однієї картки (лист Nanesi п.12)."
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
                "shade_hex": "#F0DCC8",
                "volume": "15 г + рефіл 15 г",
                "cost_price": Decimal("978.00"),
                "retail_price": Decimal("1350.00"),
                "sale_price": None,
                "stock_quantity": 15,
            },
            {
                "sku": "8809563103362",
                "barcode": "8809563103362",
                "shade": "№21 Light Beige",
                "shade_hex": "#E4C4A8",
                "volume": "15 г + рефіл 15 г",
                "cost_price": Decimal("978.00"),
                "retail_price": Decimal("1350.00"),
                "sale_price": None,
                "stock_quantity": 8,
            },
            {
                "sku": "8809563103379",
                "barcode": "8809563103379",
                "shade": "№23 Natural Beige",
                "shade_hex": "#D4A882",
                "volume": "15 г + рефіл 15 г",
                "cost_price": Decimal("978.00"),
                "retail_price": Decimal("1350.00"),
                "sale_price": None,
                "stock_quantity": 0,
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
    {
        "icon_label": "leaf",
        "title": "Оригінальна продукція",
        "text": "100% гарантія якості",
        "sort_order": 1,
    },
    {
        "icon_label": "truck",
        "title": "Безкоштовна доставка",
        "text": "від 1500\xa0грн",
        "sort_order": 2,
    },
    {
        "icon_label": "award",
        "title": "Офіційні постачальники",
        "text": "напряму з Кореї",
        "sort_order": 3,
    },
    {
        "icon_label": "refresh",
        "title": "14 днів на повернення",
        "text": "та обмін",
        "sort_order": 4,
    },
    {
        "icon_label": "headset",
        "title": "Підтримка 24/7",
        "text": "ми завжди поруч",
        "sort_order": 5,
    },
]

# Слайди 2–3 (слайд 1 збирається з SiteSettings у seed_demo)
HERO_BANNERS_STOCK = [
    {
        "sort_order": 2,
        "eyebrow": "K-Beauty догляд",
        "title": "Ефективні формули для щоденного ритуалу",
        "subtitle": (
            "<p>Ніжний догляд і видимий результат: сироватки, SPF та креми "
            "від перевірених корейських брендів.</p>"
        ),
        "button_text": "Дивитись догляд",
        "button_url": "/katalog/",
        "overlay_blur": 8,
        "overlay_opacity": 70,
        "title_ru": "Эффективные формулы для ежедневного ритуала",
        "subtitle_ru": (
            "<p>Нежный уход и видимый результат: сыворотки, SPF и кремы "
            "от проверенных корейских брендов.</p>"
        ),
        "button_text_ru": "Смотреть уход",
        "eyebrow_ru": "K-Beauty уход",
        "title_en": "Effective formulas for your daily ritual",
        "subtitle_en": (
            "<p>Gentle care and visible results: serums, SPF and creams "
            "from trusted Korean brands.</p>"
        ),
        "button_text_en": "Shop skincare",
        "eyebrow_en": "K-Beauty care",
    },
    {
        "sort_order": 3,
        "eyebrow": "Акції місяця",
        "title": "Краса без компромісів — вигідні пропозиції",
        "subtitle": (
            "<p>Підбірка акційних позицій з тестового асортименту. "
            "Оновлюйте тексти та зображення в адмінці будь-коли.</p>"
        ),
        "button_text": "До акцій",
        "button_url": "/dobirka/aktsii/",
        "overlay_blur": 12,
        "overlay_opacity": 68,
        "title_ru": "Красота без компромиссов — выгодные предложения",
        "subtitle_ru": (
            "<p>Подборка акционных позиций из тестового ассортимента. "
            "Обновляйте тексты и изображения в админке в любое время.</p>"
        ),
        "button_text_ru": "К акциям",
        "eyebrow_ru": "Акции месяца",
        "title_en": "Beauty without compromise — special offers",
        "subtitle_en": (
            "<p>A selection of promo items from the demo catalog. "
            "Update copy and images in the admin anytime.</p>"
        ),
        "button_text_en": "View sale",
        "eyebrow_en": "This month’s deals",
    },
]
