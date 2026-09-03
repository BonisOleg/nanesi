from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from src.commerce.models import (
    Cart, CartItem, Order, OrderIntegrationEvent, OrderItem, OrderStatusLog, PromoCode,
)
from src.commerce.services import OrderStatusError, change_order_status


class CartItemInline(TabularInline):
    model = CartItem
    extra = 0
    autocomplete_fields = ["product_variant"]
    readonly_fields = ["added_at"]


@admin.register(Cart)
class CartAdmin(ModelAdmin):
    """Довідково/дебаг — кошики створюються автоматично на вітрині."""

    list_display = ("pk", "user", "session_key", "status", "contact_phone", "updated_at")
    list_filter = ("status",)
    search_fields = (
        "session_key", "user__username", "user__email",
        "contact_full_name", "contact_phone", "contact_email",
    )
    inlines = [CartItemInline]
    readonly_fields = ["created_at", "updated_at"]
    fieldsets = (
        (None, {"fields": ("user", "session_key", "status", "promo_code")}),
        ("Контакти з checkout (покинутий кошик)", {
            "fields": ("contact_full_name", "contact_phone", "contact_email"),
        }),
        ("Службові", {"fields": ("created_at", "updated_at")}),
    )


@admin.register(PromoCode)
class PromoCodeAdmin(ModelAdmin):
    list_display = ("code", "discount_type", "discount_value", "used_count", "max_uses", "is_active")
    list_filter = ("discount_type", "is_active")
    search_fields = ("code",)
    readonly_fields = ["used_count", "created_at", "updated_at"]


class OrderItemInline(TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ["product_variant", "product_name", "sku", "unit_price", "qty", "line_total"]
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


class OrderStatusLogInline(TabularInline):
    model = OrderStatusLog
    extra = 0
    readonly_fields = ["from_status", "to_status", "note", "changed_by", "created_at"]
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


class OrderIntegrationEventInline(TabularInline):
    """Черга подій для майбутньої CRM/ERP-інтеграції (Доповнення §3) — лише перегляд."""

    model = OrderIntegrationEvent
    extra = 0
    fields = ["event_type", "status", "created_at", "sent_at", "error_message"]
    readonly_fields = fields
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = (
        "number", "full_name", "phone", "status", "payment_status",
        "payment_method", "delivery_method", "total", "created_at",
    )
    list_filter = ("status", "payment_status", "payment_method", "delivery_method")
    search_fields = ("number", "full_name", "phone", "email", "ttn_number")
    readonly_fields = [
        "number", "user", "subtotal", "discount_amount", "total",
        "payment_intent_id", "payment_idempotency_key", "paid_at",
        "ttn_number", "shipping_error", "created_at", "updated_at",
    ]
    inlines = [OrderItemInline, OrderStatusLogInline, OrderIntegrationEventInline]
    actions = [
        "mark_confirmed", "mark_paid", "mark_assembling",
        "mark_shipped", "mark_delivered", "mark_cancelled", "retry_create_ttn",
    ]

    fieldsets = (
        ("Замовлення", {"fields": ("number", "user", "status", "created_at", "updated_at")}),
        ("Контакт", {"fields": ("full_name", "phone", "email")}),
        ("Доставка", {
            "fields": (
                "delivery_method", "np_city_name", "np_city_ref",
                "np_warehouse_name", "np_warehouse_ref",
                "ukrposhta_index", "ukrposhta_address",
                "ttn_number", "shipping_error",
            ),
        }),
        ("Оплата", {
            "fields": (
                "payment_method", "payment_status", "payment_intent_id",
                "payment_idempotency_key", "paid_at",
            ),
        }),
        ("Суми", {"fields": ("subtotal", "discount_amount", "shipping_cost", "total", "promo_code_snapshot")}),
        ("Коментар", {"fields": ("comment",)}),
    )

    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj))
        if obj is not None:
            # статус змінюється лише через change_order_status (матриця переходів),
            # не прямим редагуванням поля в адмінці (ERR-BIZ-08).
            readonly.append("status")
        return readonly

    def _bulk_change_status(self, request, queryset, to_status: str, label: str):
        """Статус змінюється ЛИШЕ через change_order_status (матриця ALLOWED_TRANSITIONS,
        ERR-BIZ-08) — ніколи прямим редагуванням поля в адмінці."""
        done, failed = 0, 0
        for order in queryset:
            try:
                change_order_status(order, to_status, user=request.user, note="Змінено з адмінки")
                done += 1
            except OrderStatusError as exc:
                failed += 1
                self.message_user(request, f"{order.number}: {exc}", level="warning")
        self.message_user(request, f"{label}: {done}, пропущено (заборонений перехід): {failed}")

    @admin.action(description="Статус → Підтверджено")
    def mark_confirmed(self, request, queryset):
        self._bulk_change_status(request, queryset, Order.Status.CONFIRMED, "Підтверджено")

    @admin.action(description="Статус → Оплачено")
    def mark_paid(self, request, queryset):
        self._bulk_change_status(request, queryset, Order.Status.PAID, "Оплачено")

    @admin.action(description="Статус → Збирається")
    def mark_assembling(self, request, queryset):
        self._bulk_change_status(request, queryset, Order.Status.ASSEMBLING, "У зборці")

    @admin.action(description="Статус → Відправлено")
    def mark_shipped(self, request, queryset):
        self._bulk_change_status(request, queryset, Order.Status.SHIPPED, "Відправлено")

    @admin.action(description="Статус → Доставлено")
    def mark_delivered(self, request, queryset):
        self._bulk_change_status(request, queryset, Order.Status.DELIVERED, "Доставлено")

    @admin.action(description="Статус → Скасовано")
    def mark_cancelled(self, request, queryset):
        self._bulk_change_status(request, queryset, Order.Status.CANCELLED, "Скасовано")

    @admin.action(description="Створити ТТН повторно")
    def retry_create_ttn(self, request, queryset):
        from src.shipping.services import ShippingError, create_ttn

        done, failed = 0, 0
        for order in queryset:
            try:
                create_ttn(order.pk)
                done += 1
            except ShippingError as exc:
                failed += 1
                self.message_user(request, f"{order.number}: {exc}", level="warning")
        self.message_user(request, f"ТТН створено: {done}, помилок: {failed}")


@admin.register(OrderIntegrationEvent)
class OrderIntegrationEventAdmin(ModelAdmin):
    """Черга подій для CRM/ERP (KeyCRM/SalesDrive, Доповнення §3) — «розетка в коді»,
    без живого API. Лише перегляд: події пише queue_order_event(), не адмін."""

    list_display = ("order", "event_type", "status", "created_at", "sent_at")
    list_filter = ("event_type", "status")
    search_fields = ("order__number",)
    readonly_fields = ("order", "event_type", "payload", "status", "error_message", "created_at", "sent_at", "updated_at")

    def has_add_permission(self, request) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False
