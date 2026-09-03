"""Replace ₴ with грн in SiteSettings promo texts; update field labels."""

from django.db import migrations, models
from decimal import Decimal


def replace_hryvnia_symbol(apps, schema_editor):
    SiteSettings = apps.get_model("content", "SiteSettings")
    fields = (
        "topbar_promo_text",
        "topbar_promo_text_uk",
        "topbar_promo_text_ru",
        "topbar_promo_text_en",
    )
    nbsp = "\xa0"
    for site in SiteSettings.objects.all():
        changed = False
        for name in fields:
            if not hasattr(site, name):
                continue
            value = getattr(site, name)
            if not value:
                continue
            new_value = value.replace("₴", "грн").replace(" грн", f"{nbsp}грн")
            if new_value != value:
                setattr(site, name, new_value)
                changed = True
        if changed:
            site.save(update_fields=[n for n in fields if hasattr(site, n)])


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0009_sitesettings_thank_you_phone_help"),
    ]

    operations = [
        migrations.RunPython(replace_hryvnia_symbol, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="sitesettings",
            name="free_shipping_threshold",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                default=Decimal("1500.00"),
                help_text=(
                    "Поріг для прогрес-бару в кошику: «До безкоштовної доставки залишилось … грн». "
                    "Порожнє поле — бар не показується. Текст верхньої смужки оновіть окремо."
                ),
                max_digits=10,
                null=True,
                verbose_name="Сума безкоштовної доставки, грн",
            ),
        ),
        migrations.AlterField(
            model_name="sitesettings",
            name="topbar_promo_text",
            field=models.CharField(
                blank=True,
                default="Безкоштовна доставка від 1500\xa0грн",
                max_length=255,
                verbose_name="Текст верхньої смужки",
            ),
        ),
    ]
