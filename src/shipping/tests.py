from unittest.mock import patch

import requests
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from src.shipping.client import NovaPoshtaClient, NovaPoshtaError
from src.shipping.models import NPCity, NPWarehouse
from src.shipping.selectors import CITY_SUGGESTIONS_LIMIT, search_cities, search_warehouses
from src.shipping.utils import translit_kmu2010


class NPCitySearchTests(TestCase):
    def test_kyiv_ranks_above_oblast_substring_matches(self):
        """«киї» має віддати Київ раніше за села з «Київська» у назві."""
        NPCity.objects.create(ref="a1", name="Андріївка (Київська обл.)", area="Київська")
        NPCity.objects.create(ref="a2", name="Антонівка (Київська обл.)", area="Київська")
        NPCity.objects.create(ref="kyiv", name="Київ", area="Київська")
        NPCity.objects.create(ref="kyivka", name="Київка", area="Полтавська")

        names = [c.name for c in search_cities("киї")]
        self.assertEqual(names[0], "Київ")
        self.assertIn("Київка", names)
        self.assertLess(names.index("Київ"), names.index("Київка"))
        self.assertLess(names.index("Київка"), names.index("Андріївка (Київська обл.)"))

    def test_city_search_returns_all_matches_without_cap(self):
        # Вимога змінилась (P2, 40 КБ відповіді): UI-пошук міст ріжеться до 40.
        # limit=None лишає повний список — на початкових 35 збігах це все ще 35.
        for i in range(35):
            NPCity.objects.create(ref=f"c-{i}", name=f"Тестмісто {i:02d}")
        self.assertEqual(len(list(search_cities("тестмісто", limit=None))), 35)

        for i in range(35, 45):
            NPCity.objects.create(ref=f"c-{i}", name=f"Тестмісто {i:02d}")
        capped = list(search_cities("тестмісто"))
        self.assertLessEqual(len(capped), 40)
        self.assertEqual(len(capped), CITY_SUGGESTIONS_LIMIT)
        self.assertEqual(len(list(search_cities("тестмісто", limit=None))), 45)

    def test_typographic_apostrophe_finds_kamianets(self):
        """НП зберігає ASCII ', користувач часто вводить ’ (U+2019) або ʼ (U+02BC)."""
        NPCity.objects.create(ref="kp", name="Кам'янець-Подільський", area="Хмельницька")
        for query in ("Кам\u2019янець", "Кам\u02bcянець"):
            with self.subTest(query=query):
                names = [city.name for city in search_cities(query)]
                self.assertIn("Кам'янець-Подільський", names)

    def test_latin_exonyms_rank_major_cities_first(self):
        samples = (
            ("kyiv", "Київ"),
            ("kyivka", "Київка"),
            ("lviv", "Львів"),
            ("odesa", "Одеса"),
            ("kharkiv", "Харків"),
            ("zaporizhzhia", "Запоріжжя"),
            ("dnipro", "Дніпро"),
            ("mykolaiv", "Миколаїв"),
            ("rivne", "Рівне"),
            ("chernihiv", "Чернігів"),
            ("ivano", "Івано-Франківськ"),
            ("khmel", "Хмельницький"),
        )
        for ref, name in samples:
            NPCity.objects.create(ref=ref, name=name)

        for query in ("Kyiv", "Kiev", "KYIV"):
            with self.subTest(query=query):
                names = [city.name for city in search_cities(query)]
                self.assertEqual(names[0], "Київ")
                self.assertIn("Київка", names)

        expectations = {
            "Lviv": "Львів",
            "Lvov": "Львів",
            "Odessa": "Одеса",
            "Kharkov": "Харків",
            "Zaporozhye": "Запоріжжя",
            "Zaporozhe": "Запоріжжя",
            "Zaporizhia": "Запоріжжя",
            "Dnepr": "Дніпро",
            "Dnipropetrovsk": "Дніпро",
            "Nikolaev": "Миколаїв",
            "Rovno": "Рівне",
            "Chernigov": "Чернігів",
            "Ivano-Frankovsk": "Івано-Франківськ",
            "Khmelnitsky": "Хмельницький",
        }
        for query, expected in expectations.items():
            with self.subTest(query=query):
                names = [city.name for city in search_cities(query)]
                self.assertTrue(names)
                self.assertEqual(names[0], expected)

    def test_np_cities_view_latin_kyiv(self):
        NPCity.objects.create(ref="kyiv", name="Київ", area="Київська")
        NPCity.objects.create(ref="kyivka", name="Київка", area="Полтавська")
        response = self.client.get(reverse("shipping:np_cities"), {"q": "Kyiv"})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["configured"])
        self.assertEqual(payload["results"][0]["name"], "Київ (Київська)")
        self.assertEqual(payload["results"][0]["ref"], "kyiv")

    def test_latin_kyi_and_lviv_match_name_latin(self):
        """«Kyi» / «lviv» знаходять місто по name_latin, без пошуку по кириличній name."""
        kyiv = NPCity.objects.create(ref="kyiv", name="Київ", area="Київська")
        lviv = NPCity.objects.create(ref="lviv", name="Львів", area="Львівська")
        self.assertEqual(kyiv.name_latin, "kyiv")
        self.assertEqual(lviv.name_latin, "lviv")

        NPCity.objects.filter(pk=kyiv.pk).update(name_latin="")
        self.assertEqual([city.ref for city in search_cities("Kyi")], [])
        NPCity.objects.filter(pk=kyiv.pk).update(name_latin="kyiv")

        NPCity.objects.filter(pk=lviv.pk).update(name_latin="")
        self.assertEqual([city.ref for city in search_cities("lviv")], [])
        NPCity.objects.filter(pk=lviv.pk).update(name_latin="lviv")

        self.assertEqual([city.ref for city in search_cities("Kyi")], ["kyiv"])
        self.assertEqual([city.ref for city in search_cities("lviv")], ["lviv"])

        for query, ref in (("Kyi", "kyiv"), ("lviv", "lviv")):
            response = self.client.get(reverse("shipping:np_cities"), {"q": query})
            self.assertEqual(response.status_code, 200)
            results = response.json()["results"]
            self.assertEqual(results[0]["ref"], ref)
            self.assertEqual(results[0]["name"].split(" (", 1)[0], "Київ" if ref == "kyiv" else "Львів")

    def test_latin_kyi_ranks_kyiv_above_skyi_towns(self):
        """«Kyi» віддає Київ першим, навіть якщо «kyi» є всередині -skyi."""
        NPCity.objects.create(ref="kyiv", name="Київ", area="Київська")
        NPCity.objects.create(ref="kp", name="Кам'янець-Подільський", area="Хмельницька")
        NPCity.objects.create(ref="khm", name="Хмельницький", area="Хмельницька")
        NPCity.objects.create(ref="nv", name="Новоград-Волинський", area="Житомирська")

        names = [city.name for city in search_cities("Kyi")]
        self.assertEqual(names[0], "Київ")
        for town in ("Кам'янець-Подільський", "Хмельницький", "Новоград-Волинський"):
            self.assertIn(town, names)
            self.assertLess(names.index("Київ"), names.index(town))

    def test_cyrillic_word_start_ranks_above_midword(self):
        """«Цер»: початок слова після пробілу вище за «цер» всередині слова."""
        NPCity.objects.create(ref="bts", name="Біла Церква", area="Київська")
        NPCity.objects.create(ref="mats", name="Мацерівка", area="Київська")

        names = [city.name for city in search_cities("Цер")]
        self.assertIn("Біла Церква", names)
        self.assertIn("Мацерівка", names)
        self.assertLess(names.index("Біла Церква"), names.index("Мацерівка"))

    def test_migration_backfill_fills_name_latin(self):
        import importlib

        from django.apps import apps

        migration = importlib.import_module("src.shipping.migrations.0003_npcity_name_latin")
        city = NPCity.objects.create(ref="backfill", name="Львів")
        NPCity.objects.filter(pk=city.pk).update(name_latin="")
        migration.backfill_name_latin(apps, None)
        city.refresh_from_db()
        self.assertEqual(city.name_latin, "lviv")


class TranslitKmu2010Tests(SimpleTestCase):
    def test_official_examples(self):
        samples = {
            "Київ": "kyiv",
            "Львів": "lviv",
            "Одеса": "odesa",
            "Харків": "kharkiv",
            "Запоріжжя": "zaporizhzhia",
            "Ізмаїл": "izmail",
            "Яремче": "yaremche",
            "Згурівка": "zghurivka",
            "Кам'янець-Подільський": "kamianets-podilskyi",
            "Єнакієве": "yenakiieve",
            "Ґалаґан": "galagan",
        }
        for name, latin in samples.items():
            with self.subTest(name=name):
                self.assertEqual(translit_kmu2010(name), latin)

    def test_frozen_migration_translit_matches_live(self):
        """Знімок у міграції збігається з живою translit_kmu2010 на контрольному списку."""
        import importlib

        migration = importlib.import_module("src.shipping.migrations.0003_npcity_name_latin")
        names = (
            "Київ",
            "Львів",
            "Харків",
            "Біла Церква",
            "Запоріжжя",
            "Кам'янець-Подільський",
            "Їжакевичі",
            "Ґалаґани",
            "Знам'янка",
            "Щорс",
            "Яготин",
            "Юріївка",
            "Згурівка",
        )
        for name in names:
            with self.subTest(name=name):
                self.assertEqual(migration.translit_kmu2010(name), translit_kmu2010(name))


class SyncCitiesLatinTests(TestCase):
    def test_sync_cities_fills_name_latin_without_live_api(self):
        from src.shipping.services import sync_cities

        with patch("src.shipping.services.get_client") as get_client:
            get_client.return_value.get_cities.side_effect = [
                [{
                    "Ref": "kyiv-ref",
                    "Description": "Київ",
                    "AreaDescription": "Київська",
                }],
                [],
            ]
            saved = sync_cities()
        self.assertEqual(saved, 1)
        city = NPCity.objects.get(ref="kyiv-ref")
        self.assertEqual(city.name_latin, "kyiv")
        get_client.assert_called_once()


class NPWarehouseDisplayTests(TestCase):
    def setUp(self):
        self.city = NPCity.objects.create(ref="city-1", name="Київ")

    def test_postomat_gets_label_when_missing_in_description(self):
        point = NPWarehouse.objects.create(
            ref="p-1", city=self.city, number="1",
            description="вул. Хрещатик, 1", category="Postomat",
        )
        self.assertTrue(point.is_postomat)
        self.assertIn("Поштомат", point.display_name())

    def test_postomat_does_not_duplicate_label(self):
        point = NPWarehouse.objects.create(
            ref="p-2", city=self.city, number="2",
            description="Поштомат №2: вул. Хрещатик, 2", category="Postomat",
        )
        self.assertEqual(point.display_name(), "Поштомат №2: вул. Хрещатик, 2")

    def test_search_excludes_cargo_and_lists_postomats_after_branches(self):
        NPWarehouse.objects.create(
            ref="c-1", city=self.city, number="90",
            description="Вантажне", category="Cargo",
        )
        NPWarehouse.objects.create(
            ref="b-1", city=self.city, number="12",
            description="Відділення №12", category="Branch",
        )
        NPWarehouse.objects.create(
            ref="p-3", city=self.city, number="3",
            description="Поштомат №3", category="Postomat",
        )
        results = list(search_warehouses(self.city.pk))
        refs = [row.ref for row in results]
        self.assertEqual(refs, ["b-1", "p-3"])

    def test_numeric_query_ranks_exact_number_first(self):
        NPWarehouse.objects.create(
            ref="b-112", city=self.city, number="112",
            description="Відділення №112 (до 10 кг)", category="Branch",
        )
        NPWarehouse.objects.create(
            ref="b-12", city=self.city, number="12",
            description="Відділення №12: вул. Родини Бунге, 8", category="Branch",
        )
        NPWarehouse.objects.create(
            ref="b-10212", city=self.city, number="10212",
            description="Пункт №10212", category="Branch",
        )
        refs = [row.ref for row in search_warehouses(self.city.pk, "12")]
        self.assertEqual(refs[0], "b-12")
        self.assertLess(refs.index("b-12"), refs.index("b-112"))

    def test_warehouse_suggestions_are_capped(self):
        for i in range(55):
            NPWarehouse.objects.create(
                ref=f"b-{i}", city=self.city, number=str(i),
                description=f"Відділення №{i}", category="Branch",
            )
        self.assertEqual(len(list(search_warehouses(self.city.pk))), 40)
        self.assertEqual(len(list(search_warehouses(self.city.pk, limit=None))), 55)


@override_settings(NP_API_KEY="test-only-np-key")
class NPWarehousesTimeoutTests(TestCase):
    def test_timeout_without_warehouses_returns_unavailable(self):
        city = NPCity.objects.create(ref="empty-city", name="Порожнє")
        with patch("src.shipping.client.requests.post", side_effect=requests.Timeout("timeout")):
            response = self.client.get(reverse("shipping:np_warehouses"), {"city": city.pk})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"configured": True, "results": [], "error": "np_unavailable"},
        )

    def test_timeout_with_warehouses_returns_cached(self):
        """Порожня category змушує повторний синк: таймаут не має ховати вже збережені відділення."""
        city = NPCity.objects.create(ref="cached-city", name="Київ")
        NPWarehouse.objects.create(
            ref="w-cached", city=city, number="5",
            description="Відділення №5", category="",
        )
        with patch("src.shipping.client.requests.post", side_effect=requests.Timeout("timeout")) as post:
            response = self.client.get(reverse("shipping:np_warehouses"), {"city": city.pk})
        self.assertTrue(post.called)
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["configured"])
        self.assertEqual([row["ref"] for row in payload["results"]], ["w-cached"])
        self.assertNotIn("error", payload)


class NovaPoshtaClientCallTests(TestCase):
    def test_call_wraps_timeout_into_nova_poshta_error(self):
        client = NovaPoshtaClient("test-key")
        with patch("src.shipping.client.requests.post", side_effect=requests.Timeout("timeout")) as post:
            with self.assertLogs("src.shipping.client", level="WARNING"):
                with self.assertRaises(NovaPoshtaError):
                    client.call("Address", "getWarehouses", {"CityRef": "city-ref"})
        self.assertEqual(post.call_args.kwargs["timeout"], (5, 10))


class CheckoutCityInputScriptTests(TestCase):
    def test_served_checkout_js_does_not_rewrite_latin_city_input(self):
        """Немає JS-раннера: віддана сторінка і checkout.js не транслітерують значення поля."""
        from decimal import Decimal
        from pathlib import Path

        from django.contrib.staticfiles import finders

        from src.catalog.models import Brand, Category, Product, ProductVariant

        brand = Brand.objects.create(name="NPCity", slug="np-city-input-brand")
        category = Category.objects.create(name="NPCity", slug="np-city-input-cat")
        product = Product.objects.create(
            name="NPCity", slug="np-city-input-product", brand=brand, category=category, is_active=True,
        )
        variant = ProductVariant.objects.create(
            product=product, sku="SKU-NP-CITY-INPUT", retail_price=Decimal("100.00"),
            stock_quantity=3, is_active=True,
        )
        self.client.post(reverse("commerce:cart_add", args=[variant.pk]), {"qty": 1})
        page = self.client.get(reverse("commerce:checkout"))
        self.assertEqual(page.status_code, 200)
        html = page.content.decode()
        self.assertIn("js/checkout.js", html)
        self.assertIn('id="id_np_city_name"', html)
        self.assertIn('id="np-city-suggestions"', html)
        self.assertNotIn("йцукен", html)
        self.assertNotIn("qwertyuiop", html.lower())

        js_path = finders.find("js/checkout.js")
        self.assertTrue(js_path)
        source = Path(js_path).read_text(encoding="utf-8")
        start = source.index("cityInput.addEventListener('input'")
        end = source.index("timer = setTimeout", start)
        handler = source[start:end]
        self.assertIn("var query = cityInput.value.trim();", handler)
        self.assertNotIn("cityInput.value =", handler)
        lowered = source.lower()
        for token in (
            "qwertyuiop", "йцукен", "latintocyr", "tocyrillic",
            "fixlayout", "convertlayout", "keyboardlayout",
        ):
            self.assertNotIn(token, lowered)
