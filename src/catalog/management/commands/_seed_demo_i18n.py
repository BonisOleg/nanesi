"""RU/EN поля modeltranslation для seed_demo (демо-вітрина)."""

# SiteSettings — міграційні дефолти були uk у всіх мовах
SITE_SETTINGS_I18N = {
    "topbar_promo_text_uk": "Безкоштовна доставка від 1500\xa0грн",
    "topbar_promo_text_ru": "Бесплатная доставка от 1500\xa0грн",
    "topbar_promo_text_en": "Free shipping from 1500 UAH",
    "hero_title_uk": "Косметика для вашої природної краси",
    "hero_title_ru": "Косметика для вашей естественной красоты",
    "hero_title_en": "Cosmetics for your natural beauty",
    "hero_subtitle_uk": (
        "<p>Мультибрендовий магазин догляду та макіяжу. "
        "Підібрані формули, прозорі склади та зручна доставка по Україні.</p>"
    ),
    "hero_subtitle_ru": (
        "<p>Мультибрендовый магазин ухода и макияжа. "
        "Подобранные формулы, прозрачный состав и удобная доставка по Украине.</p>"
    ),
    "hero_subtitle_en": (
        "<p>A multi-brand store for skincare and makeup. "
        "Curated formulas, transparent ingredients and convenient delivery across Ukraine.</p>"
    ),
    "work_hours_uk": "Пн–Нд 10:00–20:00",
    "work_hours_ru": "Пн–Вс 10:00–20:00",
    "work_hours_en": "Mon–Sun 10:00–20:00",
    "address_uk": "Київ, Україна",
    "address_ru": "Киев, Украина",
    "address_en": "Kyiv, Ukraine",
    "bank_transfer_details_uk": (
        "<p><strong>Отримувач:</strong> ФОП Тестовий Іван Іванович</p>"
        "<p><strong>ІПН:</strong> 1234567890</p>"
        "<p><strong>IBAN:</strong> UA123456789012345678901234567</p>"
        "<p><strong>Банк:</strong> АТ «ТестБанк»</p>"
        "<p><strong>Призначення:</strong> Оплата замовлення (вкажіть номер)</p>"
    ),
    "bank_transfer_details_ru": (
        "<p><strong>Получатель:</strong> ФОП Тестовый Иван Иванович</p>"
        "<p><strong>ИНН:</strong> 1234567890</p>"
        "<p><strong>IBAN:</strong> UA123456789012345678901234567</p>"
        "<p><strong>Банк:</strong> АО «ТестБанк»</p>"
        "<p><strong>Назначение:</strong> Оплата заказа (укажите номер)</p>"
    ),
    "bank_transfer_details_en": (
        "<p><strong>Recipient:</strong> FOP Testovyi Ivan Ivanovych</p>"
        "<p><strong>Tax ID:</strong> 1234567890</p>"
        "<p><strong>IBAN:</strong> UA123456789012345678901234567</p>"
        "<p><strong>Bank:</strong> JSC «TestBank»</p>"
        "<p><strong>Payment purpose:</strong> Order payment (include order number)</p>"
    ),
}

# зворотна сумісність імпортів
TOPBAR_PROMO_I18N = {
    k: v for k, v in SITE_SETTINGS_I18N.items() if k.startswith("topbar_promo_text_")
}

BLOG_POSTS_I18N = {
    "blog-1": {
        "title_ru": "Блог 1",
        "title_en": "Blog 1",
        "body_ru": "<p>Демо-статья для проверки блога на витрине.</p>",
        "body_en": "<p>Demo article to verify the storefront blog.</p>",
    },
    "blog-2": {
        "title_ru": "Блог-2",
        "title_en": "Blog 2",
        "body_ru": "<p>Вторая демо-статья блога NANESI.</p>",
        "body_en": "<p>Second NANESI demo blog article.</p>",
    },
}

CATEGORIES_I18N = {
    "doglyad-za-oblychchyam": {
        "name_ru": "Уход за лицом",
        "name_en": "Face care",
    },
    "kremy-dlya-oblychchya": {
        "name_ru": "Кремы для лица",
        "name_en": "Face creams",
    },
    "syrovatky-ampuly": {
        "name_ru": "Сыворотки / ампулы",
        "name_en": "Serums / ampoules",
    },
    "ochyshchennya": {
        "name_ru": "Очищение",
        "name_en": "Cleansing",
    },
    "masky": {
        "name_ru": "Маски",
        "name_en": "Masks",
    },
    "makiyazh": {
        "name_ru": "Макияж",
        "name_en": "Makeup",
    },
    "tonalni-kushony": {
        "name_ru": "Тональные средства / Кушоны",
        "name_en": "Foundations / Cushions",
    },
    "pomady": {
        "name_ru": "Помады",
        "name_en": "Lipsticks",
    },
    "rumyana": {
        "name_ru": "Румяна",
        "name_en": "Blush",
    },
    "doglyad-za-tilom": {
        "name_ru": "Уход за телом",
        "name_en": "Body care",
    },
    "doglyad-za-volossyam": {
        "name_ru": "Уход за волосами",
        "name_en": "Hair care",
    },
    "shampuni": {
        "name_ru": "Шампуни",
        "name_en": "Shampoos",
    },
    "soncezahyst-spf": {
        "name_ru": "Солнцезащита SPF",
        "name_en": "Sun protection SPF",
    },
    "spf-dlya-oblychchya": {
        "name_ru": "Для лица",
        "name_en": "For face",
    },
    "nabory-ta-miniatyury": {
        "name_ru": "Наборы и миниатюры",
        "name_en": "Sets and minis",
    },
    "k-beauty": {
        "name_ru": "K-Beauty",
        "name_en": "K-Beauty",
    },
}

BRANDS_I18N = {
    "k-beauty": {"name_ru": "K-Beauty", "name_en": "K-Beauty"},
    "purito-seoul": {"name_ru": "Purito Seoul", "name_en": "Purito Seoul"},
    "whocares": {"name_ru": "WhoCares", "name_en": "WhoCares"},
}

COLLECTIONS_I18N = {
    "hity": {"name_ru": "Хиты продаж", "name_en": "Bestsellers"},
    "novynky": {"name_ru": "Новинки", "name_en": "New arrivals"},
    "aktsii": {"name_ru": "Акции", "name_en": "Sale"},
    "makiyazh-z-spf": {"name_ru": "Макияж с SPF", "name_en": "Makeup with SPF"},
}

TRUST_I18N = {
    1: {
        "title_ru": "Оригинальная продукция",
        "title_en": "Authentic products",
        "text_ru": "100% гарантия качества",
        "text_en": "100% quality guarantee",
    },
    2: {
        "title_ru": "Бесплатная доставка",
        "title_en": "Free shipping",
        "text_ru": "от 1500\xa0грн",
        "text_en": "from 1500 UAH",
    },
    3: {
        "title_ru": "Проверенные поставщики",
        "title_en": "Verified suppliers",
        "text_ru": "оригинальная продукция",
        "text_en": "authentic products",
    },
    4: {
        "title_ru": "Обмен и возврат",
        "title_en": "Exchange and returns",
        "text_ru": "согласно законодательству",
        "text_en": "as required by law",
    },
    5: {
        "title_ru": "Поддержка каждый день",
        "title_en": "Support every day",
        "text_ru": "Пн–Вс 10:00–20:00",
        "text_en": "Mon–Sun 10:00–20:00",
    },
}

ATTR_GROUPS_I18N = {
    "skin_type": {"name_ru": "Тип кожи", "name_en": "Skin type"},
    "concern": {"name_ru": "Проблема / назначение", "name_en": "Concern / purpose"},
    "country": {"name_ru": "Страна / направление", "name_en": "Country / origin"},
    "ingredient": {"name_ru": "Ингредиенты", "name_en": "Ingredients"},
    "age": {"name_ru": "Возраст", "name_en": "Age"},
    "spf": {"name_ru": "SPF", "name_en": "SPF"},
}

# (attribute.code, value.slug) → ru/en
ATTR_VALUES_I18N = {
    ("skin_type", "all-types"): {"value_ru": "Все типы", "value_en": "All types"},
    ("skin_type", "sensitive"): {"value_ru": "Чувствительная", "value_en": "Sensitive"},
    ("skin_type", "dry"): {"value_ru": "Сухая", "value_en": "Dry"},
    ("skin_type", "normal"): {"value_ru": "Нормальная", "value_en": "Normal"},
    ("skin_type", "combination"): {"value_ru": "Комбинированная", "value_en": "Combination"},
    ("skin_type", "oily"): {"value_ru": "Жирная", "value_en": "Oily"},
    ("concern", "dehydration"): {"value_ru": "Обезвоженность", "value_en": "Dehydration"},
    ("concern", "dryness"): {"value_ru": "Сухость", "value_en": "Dryness"},
    ("concern", "barrier"): {"value_ru": "Ослабленный барьер", "value_en": "Weakened barrier"},
    ("concern", "wrinkles"): {"value_ru": "Мелкие морщины", "value_en": "Fine lines"},
    ("concern", "sensitivity"): {"value_ru": "Чувствительность", "value_en": "Sensitivity"},
    ("concern", "redness"): {"value_ru": "Покраснение", "value_en": "Redness"},
    ("concern", "uv-protection"): {"value_ru": "Защита от UV", "value_en": "UV protection"},
    ("concern", "photoaging"): {"value_ru": "Фотостарение", "value_en": "Photoaging"},
    ("concern", "tone"): {"value_ru": "Выравнивание тона", "value_en": "Tone evening"},
    ("concern", "scalp-balance"): {"value_ru": "Баланс кожи головы", "value_en": "Scalp balance"},
    ("country", "south-korea"): {"value_ru": "Южная Корея", "value_en": "South Korea"},
    ("country", "ukraine"): {"value_ru": "Украина", "value_en": "Ukraine"},
    ("ingredient", "niacinamide"): {"value_ru": "Ниацинамид", "value_en": "Niacinamide"},
    ("ingredient", "ceramides"): {"value_ru": "Церамиды", "value_en": "Ceramides"},
    ("ingredient", "centella"): {"value_ru": "Центелла", "value_en": "Centella"},
    ("ingredient", "panthenol"): {"value_ru": "Пантенол", "value_en": "Panthenol"},
    ("ingredient", "hyaluronic-acid"): {
        "value_ru": "Гиалуроновая кислота",
        "value_en": "Hyaluronic acid",
    },
    ("ingredient", "peptides"): {"value_ru": "Пептиды", "value_en": "Peptides"},
    ("ingredient", "pdrn"): {"value_ru": "PDRN", "value_en": "PDRN"},
    ("ingredient", "wheat-protein"): {"value_ru": "Протеин пшеницы", "value_en": "Wheat protein"},
    ("age", "all-ages"): {"value_ru": "Все возраста", "value_en": "All ages"},
    ("age", "25-plus"): {"value_ru": "25+", "value_en": "25+"},
    ("age", "35-plus"): {"value_ru": "35+", "value_en": "35+"},
    ("spf", "spf30"): {"value_ru": "SPF30", "value_en": "SPF30"},
    ("spf", "spf50-plus"): {"value_ru": "SPF50+", "value_en": "SPF50+"},
}

PAGES_I18N = {
    "pro-nas": {
        "title_ru": "О нас",
        "title_en": "About us",
        "body_ru": (
            "<p>NANESI — мультибрендовый beauty store. Мы подбираем формулы с "
            "прозрачным составом и удобной доставкой по Украине.</p>"
            "<p>Контент страницы можно заменить в админке.</p>"
        ),
        "body_en": (
            "<p>NANESI is a multi-brand beauty store. We curate formulas with "
            "transparent ingredients and convenient delivery across Ukraine.</p>"
            "<p>You can replace this page content in the admin.</p>"
        ),
    },
    "dostavka-i-oplata": {
        "title_ru": "Доставка и оплата",
        "title_en": "Shipping and payment",
        "body_ru": (
            "<p>Доставка Новой Почтой и Укрпочтой. Бесплатная доставка — "
            "от суммы, заданной в настройках сайта.</p>"
            "<p>Оплата: наложенный платёж, банковский перевод; онлайн-оплата — после "
            "подключения LiqPay.</p>"
        ),
        "body_en": (
            "<p>Delivery via Nova Poshta and Ukrposhta. Free shipping from the "
            "threshold set in site settings.</p>"
            "<p>Payment: cash on delivery, bank transfer; online card payment after "
            "LiqPay is connected.</p>"
        ),
    },
    "obmin-ta-povernennya": {
        "title_ru": "Обмен и возврат",
        "title_en": "Exchange and returns",
        "body_ru": (
            "<p>Обмен и возврат товаров осуществляются в соответствии с "
            "действующим законодательством Украины.</p>"
            "<p>Товар должен быть в оригинальной упаковке, без следов использования, "
            "с сохранёнными пломбами и ярлыками (если предусмотрены).</p>"
            "<p>Для оформления обмена или возврата обратитесь в поддержку "
            "с номером заказа.</p>"
        ),
        "body_en": (
            "<p>Exchange and returns are handled in accordance with "
            "applicable Ukrainian law.</p>"
            "<p>The item must be in original packaging, unused, with seals and "
            "labels intact where applicable.</p>"
            "<p>Contact support with your order number to start an exchange or return.</p>"
        ),
    },
    "oferta": {
        "title_ru": "Публичная оферта",
        "title_en": "Public offer",
        "body_ru": (
            "<p>Текст публичной оферты. Замените на юридический документ "
            "заказчика в админке.</p>"
        ),
        "body_en": (
            "<p>Public offer text. Replace with the merchant’s legal document "
            "in the admin.</p>"
        ),
    },
    "polityka-konfidentsiinosti": {
        "title_ru": "Политика конфиденциальности",
        "title_en": "Privacy policy",
        "body_ru": (
            "<p>Мы обрабатываем персональные данные только для выполнения заказов "
            "и обратной связи. Полный текст политики — от заказчика.</p>"
        ),
        "body_en": (
            "<p>We process personal data only to fulfil orders and provide support. "
            "The full policy text comes from the merchant.</p>"
        ),
    },
    "kontakty": {
        "title_ru": "Контакты",
        "title_en": "Contacts",
        "body_ru": (
            "<p>Свяжитесь с нами удобным способом — ответим в рабочие часы.</p>"
            "<p>Актуальные телефон, email и график также в блоке контактов ниже "
            "(управляются в настройках сайта).</p>"
        ),
        "body_en": (
            "<p>Reach out in any convenient way — we’ll reply during business hours.</p>"
            "<p>Phone, email and schedule also appear in the contacts block below "
            "(managed in site settings).</p>"
        ),
    },
}

PRODUCTS_I18N = {
    "k-beauty-ceramide-ampoule-30-ml": {
        "name_ru": "Ампула с церамидами K-Beauty Barrier Ampoule",
        "name_en": "K-Beauty Barrier Ampoule with ceramides",
        "short_description_ru": (
            "Концентрированная ампула для укрепления барьера кожи и снижения "
            "ощущения стянутости."
        ),
        "short_description_en": (
            "A concentrated ampoule to reinforce the skin barrier and ease tightness."
        ),
    },
    "k-beauty-green-tea-toner-150-ml": {
        "name_ru": "Тонер с зелёным чаем K-Beauty Green Tea Balancing Toner",
        "name_en": "K-Beauty Green Tea Balancing Toner",
        "short_description_ru": (
            "Лёгкий тонер для ежедневного восстановления pH после очищения. "
            "Подходит для комбинированной и чувствительной кожи."
        ),
        "short_description_en": (
            "A light toner to restore pH after cleansing. Suitable for combination "
            "and sensitive skin."
        ),
    },
    "k-beauty-rice-sleeping-mask-80-ml": {
        "name_ru": "Ночная маска с рисом K-Beauty Rice Sleeping Mask",
        "name_en": "K-Beauty Rice Sleeping Mask",
        "short_description_ru": (
            "Ночной уход для сияния и увлажнения. Нанести толстым слоем перед сном."
        ),
        "short_description_en": (
            "Overnight care for glow and hydration. Apply a thick layer before bed."
        ),
    },
    "purito-centella-bb-cushion-13": {
        "name_ru": "Кушон с экстрактом центеллы Purito Seoul Wonder Releaf Centella BB Cushion",
        "name_en": "Purito Seoul Wonder Releaf Centella BB Cushion",
        "short_description_ru": (
            "BB-кушон с возможностью наслаивания. Выравнивает тон и скрывает "
            "несовершенства, сохраняя естественный вид."
        ),
        "short_description_en": (
            "A buildable BB cushion that evens tone and covers imperfections "
            "while keeping a natural look."
        ),
    },
    "purito-daily-soft-touch-sunscreen-spf50": {
        "name_ru": (
            "Солнцезащитный крем с керамидами Purito Seoul Daily Soft Touch "
            "Sunscreen SPF50+ PA++++"
        ),
        "name_en": "Purito Seoul Daily Soft Touch Sunscreen SPF50+ PA++++",
        "short_description_ru": (
            "Лёгкий солнцезащитный крем широкого спектра SPF50+ PA++++ без "
            "выраженного белого следа."
        ),
        "short_description_en": (
            "A light broad-spectrum SPF50+ PA++++ sunscreen with minimal white cast."
        ),
    },
    "purito-soft-touch-blush": {
        "name_ru": "Румяна Purito Seoul Soft Touch Blush",
        "name_en": "Purito Seoul Soft Touch Blush",
        "short_description_ru": (
            "Шелковистые румяна с естественным свечением. Три цвета на одной карточке."
        ),
        "short_description_en": (
            "Silky blush with a natural glow. Three shades on one card."
        ),
    },
    "purito-wonder-releaf-centella-serum-60-ml": {
        "name_ru": (
            "Сыворотка с экстрактом центеллы без ароматизаторов Purito Seoul "
            "Wonder Releaf Centella Serum Unscented"
        ),
        "name_en": "Purito Seoul Wonder Releaf Centella Serum Unscented",
        "short_description_ru": (
            "Успокаивающая сыворотка без ароматизаторов для чувствительной кожи. "
            "Помогает уменьшать покраснение и дискомфорт."
        ),
        "short_description_en": (
            "A fragrance-free soothing serum for sensitive skin. Helps ease "
            "redness and discomfort."
        ),
    },
    "whocares-balancing-shampoo-300-ml": {
        "name_ru": "Шампунь безсульфатный whocares Balancing Shampoo",
        "name_en": "whocares Balancing Shampoo (sulfate-free)",
        "short_description_ru": (
            "Безсульфатный шампунь для деликатного очищения сухой и нормальной "
            "кожи головы."
        ),
        "short_description_en": (
            "A sulfate-free shampoo for gentle cleansing of dry and normal scalps."
        ),
    },
    "whocares-vegan-pdrn-cream-50-ml": {
        "name_ru": (
            "Увлажняющий крем для лица с веганскими полинуклеотидами "
            "whocares Vegan PDRN Cream"
        ),
        "name_en": "whocares Vegan PDRN Cream",
        "short_description_ru": (
            "Увлажняющий крем для ежедневного ухода, который помогает поддерживать "
            "защитный барьер кожи и уменьшать проявления сухости."
        ),
        "short_description_en": (
            "A daily moisturiser that helps support the skin barrier and ease dryness."
        ),
    },
    "whocares-velvet-lip-color": {
        "name_ru": "Бархатная помада whocares Velvet Lip Color",
        "name_en": "whocares Velvet Lip Color",
        "short_description_ru": (
            "Кремовое покрытие с полуматовым финишем. Четыре оттенка — отдельные SKU."
        ),
        "short_description_en": (
            "Creamy coverage with a semi-matte finish. Four shades as separate SKUs."
        ),
    },
}


def merge_i18n(defaults: dict, i18n: dict | None) -> dict:
    if i18n:
        defaults.update(i18n)
    return defaults
