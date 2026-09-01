import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    """Обране — рівень товару (Product), а не варіанту: картка товару має одну кнопку
    «В обране» незалежно від варіанту (Підетап 2). Даних ще немає в проді — без default."""

    dependencies = [
        ("accounts", "0002_initial"),
        ("catalog", "0002_productvariant_productvariant_retail_gte_cost"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="wishlist",
            name="uniq_wishlist_user_variant",
        ),
        migrations.RemoveField(
            model_name="wishlist",
            name="product_variant",
        ),
        migrations.AddField(
            model_name="wishlist",
            name="product",
            field=models.ForeignKey(
                default=None,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="wishlisted_by",
                to="catalog.product",
                verbose_name="Товар",
            ),
            preserve_default=False,
        ),
        migrations.AlterModelOptions(
            name="wishlist",
            options={"ordering": ["-created_at"], "verbose_name": "Обране", "verbose_name_plural": "Обране"},
        ),
        migrations.AddConstraint(
            model_name="wishlist",
            constraint=models.UniqueConstraint(fields=("user", "product"), name="uniq_wishlist_user_product"),
        ),
    ]
