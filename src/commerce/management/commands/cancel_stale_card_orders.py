from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from src.commerce.models import Order
from src.commerce.services import OrderStatusError, change_order_status


class Command(BaseCommand):
    help = "Скасувати неоплачені карткові замовлення старші за 60 хвилин і повернути склад"

    def add_arguments(self, parser):
        parser.add_argument("--minutes", type=int, default=60)

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(minutes=options["minutes"])
        qs = (
            Order.objects.filter(
                payment_method=Order.PaymentMethod.CARD_ONLINE,
                payment_status=Order.PaymentStatus.UNPAID,
                created_at__lt=cutoff,
            )
            .exclude(status=Order.Status.CANCELLED)
            .order_by("pk")
        )
        cancelled = 0
        for order in qs:
            try:
                change_order_status(
                    order,
                    Order.Status.CANCELLED,
                    note="Авто-скасування неоплаченої картки (60 хв)",
                )
                cancelled += 1
            except OrderStatusError as exc:
                self.stderr.write(f"{order.number}: {exc}")
        self.stdout.write(self.style.SUCCESS(f"cancelled={cancelled}"))
