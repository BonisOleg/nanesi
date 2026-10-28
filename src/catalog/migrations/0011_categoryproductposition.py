import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0010_collectionproduct_position"),
    ]

    operations = [
        migrations.CreateModel(
            name="CategoryProductPosition",
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
                ("position", models.PositiveIntegerField(default=0, verbose_name="Позиція")),
                (
                    "category",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="product_positions",
                        to="catalog.category",
                        verbose_name="Категорія",
                    ),
                ),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="category_positions",
                        to="catalog.product",
                        verbose_name="Товар",
                    ),
                ),
            ],
            options={
                "verbose_name": "Позиція товару в категорії",
                "verbose_name_plural": "Позиції товарів у категорії",
                "indexes": [
                    models.Index(
                        fields=["category", "position", "product"],
                        name="idx_category_product_position",
                    )
                ],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("category", "product"),
                        name="uniq_category_product_position",
                    )
                ],
            },
        ),
    ]
