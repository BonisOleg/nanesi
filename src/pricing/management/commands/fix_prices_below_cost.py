"""SEC-09 (shop_security_skill), шар 3: nightly-аудит товарів дешевших за собівартість.

Лише ЗВІТ — автоматично не виправляє (щоб не переписати ціну без погляду людини).
Запуск: python3 manage.py fix_prices_below_cost
"""
from django.core.management.base import BaseCommand
from django.db.models import F

from src.catalog.models import ProductVariant


class Command(BaseCommand):
    help = "Звіт: варіанти товару, де retail_price нижча за cost_price (аудит, без автофіксу)"

    def handle(self, *args, **options):
        broken = ProductVariant.objects.filter(
            cost_price__isnull=False, retail_price__lt=F("cost_price"),
        ).select_related("product")

        if not broken.exists():
            self.stdout.write(self.style.SUCCESS("Порушень не знайдено — усі ціни ≥ собівартості."))
            return

        self.stdout.write(self.style.ERROR(f"Знайдено {broken.count()} варіант(ів) нижче собівартості:"))
        for variant in broken:
            self.stdout.write(
                f"  SKU={variant.sku} | {variant.product.name} | "
                f"retail={variant.retail_price} < cost={variant.cost_price}",
            )
