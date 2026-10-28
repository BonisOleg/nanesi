from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0009_collectionproduct_through"),
    ]

    operations = [
        migrations.AddField(
            model_name="collectionproduct",
            name="position",
            field=models.PositiveIntegerField(default=0, verbose_name="Позиція"),
        ),
    ]
