from django.core.management.base import BaseCommand

from src.commerce.salesdrive_products import sync_all_variants


class Command(BaseCommand):
    help = "Upsert товарів у SalesDrive (sku, назва, ціна, залишок)"

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=None, help="Обмежити кількість варіантів")

    def handle(self, *args, **options):
        result = sync_all_variants(limit=options["limit"])
        if result.get("skipped"):
            self.stdout.write(self.style.WARNING(f"Пропущено: {result.get('reason')}"))
            return
        self.stdout.write(
            self.style.SUCCESS(
                f"SalesDrive products: synced={result['synced']} batches={result['batches']}"
            )
        )
