from django.contrib.auth.models import AbstractUser
from django.db import models

from src.core.models import TimeStampedModel


class User(AbstractUser):
    """Один User + role — без MTI Admin/Manager/Client (ecommerce_db_schema_skill)."""

    class Role(models.TextChoices):
        ADMIN = "admin", "Адміністратор"
        MANAGER = "manager", "Менеджер"
        CUSTOMER = "customer", "Покупець"

    role = models.CharField("Роль", max_length=20, choices=Role.choices, default=Role.CUSTOMER)
    phone = models.CharField(
        "Телефон", max_length=20, unique=True, null=True, blank=True,
        help_text="Формат 380XXXXXXXXX — для входу та Нової Пошти",
    )

    # Кабінет: збережені точки доставки — підказка на checkout.
    # Ref-и НП потрібні, щоб автопошук (src.shipping) підвантажив відділення/поштомат.
    saved_np_city_name = models.CharField("Збережене місто (НП)", max_length=255, blank=True)
    saved_np_city_ref = models.CharField("Ref міста (НП)", max_length=64, blank=True)
    saved_np_warehouse_name = models.CharField("Збережене відділення / поштомат (НП)", max_length=255, blank=True)
    saved_np_warehouse_ref = models.CharField("Ref відділення / поштомату (НП)", max_length=64, blank=True)
    saved_ukrposhta_index = models.CharField("Збережений індекс Укрпошти", max_length=5, blank=True)
    saved_ukrposhta_address = models.CharField("Збережена адреса Укрпошти", max_length=512, blank=True)

    class Meta:
        verbose_name = "Користувач"
        verbose_name_plural = "Користувачі"

    def __str__(self) -> str:
        return self.get_full_name() or self.email or self.username


class Wishlist(TimeStampedModel):
    """Обране: гість — localStorage на фронті (Підетап 1); тут — прив'язка до акаунту,
    на рівні товару (не варіанту) — картка товару має одну кнопку «В обране» (Підетап 2)."""

    user = models.ForeignKey(
        User, verbose_name="Користувач", on_delete=models.CASCADE, related_name="wishlist_items",
    )
    product = models.ForeignKey(
        "catalog.Product", verbose_name="Товар",
        on_delete=models.CASCADE, related_name="wishlisted_by",
    )

    class Meta:
        verbose_name = "Обране"
        verbose_name_plural = "Обране"
        constraints = [
            models.UniqueConstraint(fields=["user", "product"], name="uniq_wishlist_user_product"),
        ]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.user} → {self.product}"
