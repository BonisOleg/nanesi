from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0017_collection_home_teaser_product_similar"),
    ]

    operations = [
        migrations.AddField(
            model_name="productvariant",
            name="feed_exclude",
            field=models.BooleanField(
                default=False,
                help_text="Варіант не потрапить у XML-фід Google Merchant.",
                verbose_name="Виключити з фідів",
            ),
        ),
    ]
