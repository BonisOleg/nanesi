from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "src.core"
    verbose_name = "Ядро"

    def ready(self) -> None:
        from src.core.signals_images import connect_webp_signals

        connect_webp_signals()
