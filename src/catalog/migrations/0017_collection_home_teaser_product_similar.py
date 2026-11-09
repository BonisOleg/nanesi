# Generated manually for home_teaser + ProductSimilar

import django.db.models.deletion
from django.db import migrations, models


DEFAULT_TEASERS = {
    "hit": "Найпопулярніші засоби догляду цього місяця.",
    "new": "Свіжі надходження для щоденного ритуалу.",
    "sale": "Акційні позиції.",
    "custom": "Підбірка від NANESI.",
}


def fill_home_teasers(apps, schema_editor):
    Collection = apps.get_model("catalog", "Collection")
    for collection in Collection.objects.all():
        kind = collection.kind or "custom"
        text = DEFAULT_TEASERS.get(kind, DEFAULT_TEASERS["custom"])
        updates = {}
        if not (getattr(collection, "home_teaser", None) or "").strip():
            updates["home_teaser"] = text
        if hasattr(collection, "home_teaser_uk") and not (collection.home_teaser_uk or "").strip():
            updates["home_teaser_uk"] = text
        if updates:
            Collection.objects.filter(pk=collection.pk).update(**updates)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0016_seo_field_labels"),
    ]

    operations = [
        migrations.AddField(
            model_name="collection",
            name="home_teaser",
            field=models.CharField(
                blank=True,
                help_text="Текст під назвою промо-картки на головній. Порожнє — підставиться типовий опис за типом підбірки.",
                max_length=255,
                verbose_name="Опис на головній",
            ),
        ),
        migrations.AddField(
            model_name="collection",
            name="home_teaser_en",
            field=models.CharField(
                blank=True,
                help_text="Текст під назвою промо-картки на головній. Порожнє — підставиться типовий опис за типом підбірки.",
                max_length=255,
                null=True,
                verbose_name="Опис на головній",
            ),
        ),
        migrations.AddField(
            model_name="collection",
            name="home_teaser_ru",
            field=models.CharField(
                blank=True,
                help_text="Текст під назвою промо-картки на головній. Порожнє — підставиться типовий опис за типом підбірки.",
                max_length=255,
                null=True,
                verbose_name="Опис на головній",
            ),
        ),
        migrations.AddField(
            model_name="collection",
            name="home_teaser_uk",
            field=models.CharField(
                blank=True,
                help_text="Текст під назвою промо-картки на головній. Порожнє — підставиться типовий опис за типом підбірки.",
                max_length=255,
                null=True,
                verbose_name="Опис на головній",
            ),
        ),
        migrations.CreateModel(
            name="ProductSimilar",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("position", models.PositiveIntegerField(default=0, verbose_name="Порядок")),
                (
                    "from_product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="similar_links",
                        to="catalog.product",
                        verbose_name="Товар",
                    ),
                ),
                (
                    "to_product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="similar_targets",
                        to="catalog.product",
                        verbose_name="Схожий товар",
                    ),
                ),
            ],
            options={
                "verbose_name": "Схожі товари",
                "verbose_name_plural": "Схожі товари",
                "ordering": ["position", "pk"],
            },
        ),
        migrations.AddField(
            model_name="product",
            name="similar",
            field=models.ManyToManyField(
                blank=True,
                related_name="similar_in",
                through="catalog.ProductSimilar",
                to="catalog.product",
                verbose_name="Схожі товари",
            ),
        ),
        migrations.AddConstraint(
            model_name="productsimilar",
            constraint=models.UniqueConstraint(
                fields=("from_product", "to_product"),
                name="uniq_product_similar_pair",
            ),
        ),
        migrations.AddConstraint(
            model_name="productsimilar",
            constraint=models.CheckConstraint(
                condition=models.Q(("from_product", models.F("to_product")), _negated=True),
                name="product_similar_not_self",
            ),
        ),
        migrations.AddIndex(
            model_name="productsimilar",
            index=models.Index(fields=["from_product", "position"], name="product_similar_from_pos"),
        ),
        migrations.RunPython(fill_home_teasers, noop_reverse),
    ]
