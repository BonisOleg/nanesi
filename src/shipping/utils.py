"""Нормалізатори перед відправкою в API НП і латиниця міст за КМУ 2010."""
import re


def normalize_phone(raw: str) -> str:
    """→ '380XXXXXXXXX' без '+' і пробілів (спільний формат з TurboSMS/НП)."""
    digits = re.sub(r"\D", "", raw or "")
    if digits.startswith("0") and len(digits) == 10:
        digits = "38" + digits
    if digits.startswith("380"):
        return digits
    if len(digits) == 9:
        return "380" + digits
    return digits


def split_full_name(full_name: str) -> tuple[str, str]:
    """'Іванов Іван' → ('Іван', 'Іванов'). Без прізвища — вважаємо все ім'ям."""
    parts = (full_name or "").strip().split()
    if len(parts) >= 2:
        last_name, first_name = parts[0], " ".join(parts[1:])
        return first_name, last_name
    return (parts[0] if parts else "Клієнт"), ""


# ’ ‘ ʼ ` ´ → ASCII '. Кириличний пошук лишає апостроф (так у довіднику НП),
# латинський — прибирає, бо в КМУ 2010 апостроф не передається.
APOSTROPHE_TO_ASCII = str.maketrans({
    "\u2018": "'",
    "\u2019": "'",
    "\u02bc": "'",
    "`": "'",
    "\u00b4": "'",
})

_HYPHEN_TO_ASCII = str.maketrans({
    "\u2010": "-",
    "\u2011": "-",
    "\u2013": "-",
    "\u2014": "-",
    "\u2212": "-",
})

# Не передаються і не розривають слово (я після «'» — ia, не ya).
_KMU_OMIT = frozenset({
    "'",
    "`",
    "\u00b4",
    "\u2018",
    "\u2019",
    "\u02b9",
    "\u02bb",
    "\u02bc",
    "ь",
})

_KMU_SIMPLE = {
    "а": "a",
    "б": "b",
    "в": "v",
    "г": "h",
    "ґ": "g",
    "д": "d",
    "е": "e",
    "ж": "zh",
    "з": "z",
    "и": "y",
    "і": "i",
    "к": "k",
    "л": "l",
    "м": "m",
    "н": "n",
    "о": "o",
    "п": "p",
    "р": "r",
    "с": "s",
    "т": "t",
    "у": "u",
    "ф": "f",
    "х": "kh",
    "ц": "ts",
    "ч": "ch",
    "ш": "sh",
    "щ": "shch",
}

_KMU_INITIAL = {
    "є": "ye",
    "ї": "yi",
    "й": "y",
    "ю": "yu",
    "я": "ya",
}

_KMU_OTHER = {
    "є": "ie",
    "ї": "i",
    "й": "i",
    "ю": "iu",
    "я": "ia",
}

# Поширені екзоніми та варіанти → форма КМУ 2010 (lowercase).
_LATIN_CITY_EXONYMS = {
    "kiev": "kyiv",
    "lvov": "lviv",
    "lwow": "lviv",
    "odessa": "odesa",
    "kharkov": "kharkiv",
    "kharkow": "kharkiv",
    "zaporozhye": "zaporizhzhia",
    "zaporozhe": "zaporizhzhia",
    "zaporozhie": "zaporizhzhia",
    "zaporizhia": "zaporizhzhia",
    "zaporizhzhya": "zaporizhzhia",
    "zaporizzhia": "zaporizhzhia",
    "dnepr": "dnipro",
    "dnepropetrovsk": "dnipro",
    "dnipropetrovsk": "dnipro",
    "nikolaev": "mykolaiv",
    "nikolayev": "mykolaiv",
    "mykolayiv": "mykolaiv",
    "rovno": "rivne",
    "chernigov": "chernihiv",
    "chernigiv": "chernihiv",
    "ivano-frankovsk": "ivano-frankivsk",
    "ivano frankovsk": "ivano-frankivsk",
    "khmelnitsky": "khmelnytskyi",
    "khmelnitskiy": "khmelnytskyi",
    "khmelnitskyi": "khmelnytskyi",
    "khmelnytsky": "khmelnytskyi",
    "chernovtsy": "chernivtsi",
    "chernovtsi": "chernivtsi",
    "chernivtsy": "chernivtsi",
    "vinnitsa": "vinnytsia",
    "vinnitsya": "vinnytsia",
    "vinnytsya": "vinnytsia",
    "zhitomir": "zhytomyr",
    "zhytomir": "zhytomyr",
    "lugansk": "luhansk",
    "uzhgorod": "uzhhorod",
    "ternopol": "ternopil",
    "kirovograd": "kropyvnytskyi",
    "kirovohrad": "kropyvnytskyi",
    "kropyvnytsky": "kropyvnytskyi",
    "kremenchug": "kremenchuk",
    "cherkassy": "cherkasy",
    "cherkasi": "cherkasy",
    "krivoy rog": "kryvyi rih",
    "krivoyrog": "kryvyi rih",
    "krivoi rog": "kryvyi rih",
    "belaya tserkov": "bila tserkva",
    "belaya tserkva": "bila tserkva",
    "bila cerkva": "bila tserkva",
    "kamenets-podolsky": "kamianets-podilskyi",
    "kamenets-podolskiy": "kamianets-podilskyi",
    "kamenets-podolskyi": "kamianets-podilskyi",
    "kamyanets-podilsky": "kamianets-podilskyi",
    "kamyanets-podilskyi": "kamianets-podilskyi",
    "kamianets-podolsky": "kamianets-podilskyi",
    "kamianets-podilsky": "kamianets-podilskyi",
    "severodonetsk": "sievierodonetsk",
    "berdyansk": "berdiansk",
    "slavyansk": "sloviansk",
    "slaviansk": "sloviansk",
    "pavlograd": "pavlohrad",
    "borispol": "boryspil",
    "irpen": "irpin",
    "vyshgorod": "vyshhorod",
    "fastov": "fastiv",
    "nezhin": "nizhyn",
    "priluki": "pryluky",
    "mirgorod": "myrhorod",
    "akhtyrka": "okhtyrka",
    "chuguev": "chuhuiv",
    "kupyansk": "kupiansk",
    "izyum": "izium",
    "energodar": "enerhodar",
    "genichesk": "henichesk",
    "belgorod-dnestrovsky": "bilhorod-dnistrovskyi",
    "belgorod-dnestrovskiy": "bilhorod-dnistrovskyi",
    "mogilev-podolsky": "mohyliv-podilskyi",
    "novograd-volynsky": "novohrad-volynskyi",
    "novograd-volynskiy": "novohrad-volynskyi",
    "lisichansk": "lysychansk",
    "gorlovka": "horlivka",
    "makeevka": "makiivka",
    "makeyevka": "makiivka",
    "alexandria": "oleksandriia",
    "aleksandria": "oleksandriia",
    "oleksandriya": "oleksandriia",
    "evpatoria": "yevpatoriia",
    "feodosia": "feodosiia",
    "feodosiya": "feodosiia",
    "yuzhny": "yuzhne",
    "yuzhnyy": "yuzhne",
}


def translit_kmu2010(name: str) -> str:
    """Офіційна транслітерація української (постанова КМУ №55, 2010), lowercase.

    Є/Ї/Й/Ю/Я на початку слова — Ye/Yi/Y/Yu/Ya, всередині — ie/i/i/iu/ia.
    «зг» → zgh, щоб не зливалось із «ж» (zh). Ь і апостроф опускаються.
    """
    text = str(name or "").casefold()
    out: list[str] = []
    word_start = True
    i = 0
    length = len(text)
    while i < length:
        ch = text[i]
        if ch in _KMU_OMIT:
            i += 1
            continue
        if ch == "з" and i + 1 < length and text[i + 1] == "г":
            out.append("zgh")
            word_start = False
            i += 2
            continue
        if ch in _KMU_INITIAL:
            out.append(_KMU_INITIAL[ch] if word_start else _KMU_OTHER[ch])
            word_start = False
            i += 1
            continue
        mapped = _KMU_SIMPLE.get(ch)
        if mapped is not None:
            out.append(mapped)
            word_start = False
            i += 1
            continue
        out.append(ch)
        word_start = not ch.isalpha()
        i += 1
    return re.sub(r"\s+", " ", "".join(out)).strip()


def _apply_city_exonyms(query: str) -> str:
    """Точний екзонім або його префікс, якщо він не збігається з формою КМУ."""
    canonical = _LATIN_CITY_EXONYMS.get(query)
    if canonical:
        return canonical
    if len(query) < 3:
        return query
    targets = {
        target
        for alias, target in _LATIN_CITY_EXONYMS.items()
        if alias.startswith(query)
    }
    if len(targets) != 1:
        return query
    target = next(iter(targets))
    if target.startswith(query):
        return query
    return target


def latin_city_needle(query: str) -> str:
    """lower, без апострофів, екзоніми/префікси зведені до КМУ-форми."""
    text = str(query or "").strip().lower().translate(APOSTROPHE_TO_ASCII)
    text = text.replace("'", "")
    text = text.translate(_HYPHEN_TO_ASCII)
    text = re.sub(r"\s*-\s*", "-", text)
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return ""
    return _apply_city_exonyms(text)
