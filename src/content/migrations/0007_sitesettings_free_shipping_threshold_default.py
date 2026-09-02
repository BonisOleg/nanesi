from decimal import Decimal

from django.db import migrations, models


def fill_empty_threshold(apps, schema_editor):
    SiteSettings = apps.get_model("content", "SiteSettings")
    SiteSettings.objects.filter(free_shipping_threshold__isnull=True).update(
        free_shipping_threshold=Decimal("1500.00"),
    )


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0006_trustbadge_icon_label_key"),
    ]

    operations = [
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
                verbose_name="Сума безкоштовної доставки, ₴",
            ),
        ),
        migrations.RunPython(fill_empty_threshold, migrations.RunPython.noop),
    ]
