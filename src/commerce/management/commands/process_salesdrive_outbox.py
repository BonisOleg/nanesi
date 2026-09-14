from django.core.management.base import BaseCommand

from src.commerce.salesdrive_stub import process_pending_events


class Command(BaseCommand):
    help = "Обробити PENDING події CRM outbox (SalesDrive create/update)"

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=50)

    def handle(self, *args, **options):
        result = process_pending_events(limit=options["limit"])
        if result.get("skipped"):
            self.stdout.write(self.style.WARNING("SalesDrive: немає API URL/KEY — пропущено"))
            return
        style = self.style.SUCCESS if not result["failed"] else self.style.WARNING
        self.stdout.write(
            style(f"SalesDrive: processed={result['processed']} failed={result['failed']}")
        )
