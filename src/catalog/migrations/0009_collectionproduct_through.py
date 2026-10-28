# Through-модель на існуючій авто-таблиці M2M: у БД нічого не змінюється.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0008_attribute_translation"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name="CollectionProduct",
                    fields=[
                        (
                            "id",
                            models.BigAutoField(
                                auto_created=True,
                                primary_key=True,
                                serialize=False,
                                verbose_name="ID",
                            ),
                        ),
                        (
                            "collection",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                to="catalog.collection",
                                verbose_name="Підбірка",
                            ),
                        ),
                        (
                            "product",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                to="catalog.product",
                                verbose_name="Товар",
                            ),
                        ),
                    ],
                    options={
                        "verbose_name": "Товар у підбірці",
                        "verbose_name_plural": "Товари у підбірці",
                        "db_table": "catalog_collection_products",
                        "unique_together": {("collection", "product")},
                    },
                ),
                migrations.AlterField(
                    model_name="collection",
                    name="products",
                    field=models.ManyToManyField(
                        blank=True,
                        related_name="collections",
                        through="catalog.CollectionProduct",
                        to="catalog.product",
                        verbose_name="Товари",
                    ),
                ),
            ],
            database_operations=[],
        ),
    ]
