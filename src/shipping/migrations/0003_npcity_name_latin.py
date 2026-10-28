import re

from django.db import migrations, models

BATCH = 1000

# Заморожена копія src.shipping.utils.translit_kmu2010 на момент міграції.
# Історичний backfill не імпортує живий модуль: пізні правки КМУ не переписують знімок.

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


def backfill_name_latin(apps, schema_editor):
    """Локально з name, без API. Батчі по 1000."""
    NPCity = apps.get_model("shipping", "NPCity")
    last_pk = 0
    while True:
        batch = list(NPCity.objects.filter(pk__gt=last_pk).order_by("pk")[:BATCH])
        if not batch:
            break
        for city in batch:
            city.name_latin = translit_kmu2010(city.name)
        NPCity.objects.bulk_update(batch, ["name_latin"])
        last_pk = batch[-1].pk


class Migration(migrations.Migration):

    dependencies = [
        ("shipping", "0002_delivery_np_postomat_ukrposhta"),
    ]

    operations = [
        migrations.AddField(
            model_name="npcity",
            name="name_latin",
            field=models.CharField(
                blank=True,
                db_index=True,
                default="",
                max_length=255,
                verbose_name="Назва латиницею",
            ),
        ),
        migrations.RunPython(backfill_name_latin, migrations.RunPython.noop),
    ]
