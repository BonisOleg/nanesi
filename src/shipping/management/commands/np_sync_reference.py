"""Синк довідника міст НП (novaposhta_skill, Фаза 1). Без NP_API_KEY — явний вихід
з поясненням, БЕЗ фейкових даних (Фаза 0.5: «не прикидатися live»).

Запуск: python3 manage.py np_sync_reference
"""
from django.core.management.base import BaseCommand, CommandError

from src.shipping.services import ShippingConfigError, sync_cities


class Command(BaseCommand):
    help = "Синхронізувати довідник міст Нової Пошти (відділення підвантажуються ліниво під час checkout)"

    def handle(self, *args, **options):
        try:
            total = sync_cities()
        except ShippingConfigError as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(self.style.SUCCESS(f"Синхронізовано міст: {total}"))
