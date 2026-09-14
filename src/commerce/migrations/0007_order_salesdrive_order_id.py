from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("commerce", "0006_cart_checkout_contacts"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="salesdrive_order_id",
            field=models.PositiveIntegerField(
                blank=True,
                db_index=True,
                null=True,
                verbose_name="ID заявки SalesDrive",
            ),
        ),
    ]
