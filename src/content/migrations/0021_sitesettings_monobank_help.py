from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0020_seo_field_labels"),
    ]

    operations = [
        migrations.AlterField(
            model_name="sitesettings",
            name="card_payment_enabled",
            field=models.BooleanField(
                default=False,
                help_text="Автоматично недоступна на вітрині, поки не заповнений MONOBANK_TOKEN у .env",
                verbose_name="Оплата карткою онлайн увімкнена",
            ),
        ),
    ]
