from django.db import migrations, models

BATCH = 1000


def backfill_name_latin(apps, schema_editor):
    """Локально з name, без API. Батчі по 1000."""
    from src.shipping.utils import translit_kmu2010

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
