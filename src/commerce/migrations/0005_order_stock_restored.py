from django.db import migrations, models
from django.db.models import F


def restore_cancelled_orders_stock(apps, schema_editor):
    Order = apps.get_model("commerce", "Order")
    ProductVariant = apps.get_model("catalog", "ProductVariant")
    for order in Order.objects.filter(status="cancelled", stock_restored=False).prefetch_related("items"):
        for item in order.items.all():
            if not item.product_variant_id or not item.qty:
                continue
            ProductVariant.objects.filter(pk=item.product_variant_id).update(
                stock_quantity=F("stock_quantity") + item.qty,
            )
        order.stock_restored = True
        order.save(update_fields=["stock_restored"])


class Migration(migrations.Migration):

    dependencies = [
        ("commerce", "0004_ukrposhta_index"),
        ("catalog", "0007_productvariant_shade_swatch"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="stock_restored",
            field=models.BooleanField(
                default=False,
                help_text="True після скасування — щоб не повернути qty двічі",
                verbose_name="Залишок повернуто на склад",
            ),
        ),
        migrations.RunPython(restore_cancelled_orders_stock, migrations.RunPython.noop),
    ]
