from django.core.management.base import BaseCommand

from src.commerce.salesdrive_stub import process_pending_events


class Command(BaseCommand):
    help = "Обробити PENDING події CRM outbox (SalesDrive stub, поки немає API-ключів)"

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=50)

    def handle(self, *args, **options):
        result = process_pending_events(limit=options["limit"])
        self.stdout.write(
            self.style.SUCCESS(
                f"SalesDrive stub: processed={result['processed']} failed={result['failed']}"
            )
        )
