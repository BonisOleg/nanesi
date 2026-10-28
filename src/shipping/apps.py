from django.apps import AppConfig


class ShippingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "src.shipping"
    verbose_name = "Доставка"

    def ready(self) -> None:
        from django.db.backends.signals import connection_created

        from src.shipping.selectors import register_sqlite_np_lower

        connection_created.connect(
            register_sqlite_np_lower,
            dispatch_uid="src.shipping.register_sqlite_np_lower",
        )
