from django.contrib import admin, messages
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.db.models import QuerySet
from django.http import HttpRequest
from unfold.admin import ModelAdmin, TabularInline
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

from .models import User, Wishlist

if admin.site.is_registered(Group):
    admin.site.unregister(Group)


class WishlistInline(TabularInline):
    model = Wishlist
    extra = 0
    autocomplete_fields = ["product"]


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    """Unfold auth admin (unfold_auth_admin_skill): Base*Admin першим у MRO."""

    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm

    list_display = ("username", "email", "phone", "role", "is_staff", "is_active")
    list_filter = ("role", "is_staff", "is_active")
    search_fields = ("username", "email", "phone", "first_name", "last_name")
    inlines = [WishlistInline]

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Персональні дані", {"fields": ("first_name", "last_name", "email", "phone")}),
        ("Роль і доступи", {
            "fields": ("role", "is_active", "is_staff", "is_superuser", "groups", "user_permissions"),
        }),
        ("НП (збережене)", {
            "fields": (
                "saved_np_city_name", "saved_np_city_ref",
                "saved_np_warehouse_name", "saved_np_warehouse_ref",
            ),
        }),
        ("Укрпошта (збережене)", {"fields": ("saved_ukrposhta_index", "saved_ukrposhta_address")}),
        ("Дати", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "email", "phone", "role", "password1", "password2"),
        }),
    )

    def _blocked_delete_reason(self, request: HttpRequest, user: User) -> str | None:
        if user.pk == request.user.pk:
            return "Не можна видалити власний обліковий запис."
        if user.is_superuser and not (
            User.objects.filter(is_superuser=True).exclude(pk=user.pk).exists()
        ):
            return "Не можна видалити останнього суперкористувача."
        return None

    def has_delete_permission(self, request, obj=None):
        if obj is not None and self._blocked_delete_reason(request, obj):
            return False
        return super().has_delete_permission(request, obj)

    def delete_model(self, request, obj):
        reason = self._blocked_delete_reason(request, obj)
        if reason:
            messages.error(request, reason)
            raise PermissionDenied(reason)
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset: QuerySet[User]):
        users = list(queryset)
        blocked, allowed = [], []
        for user in users:
            if user.pk == request.user.pk:
                blocked.append((user, "не можна видалити власний обліковий запис"))
            else:
                allowed.append(user)
        allowed_ids = {u.pk for u in allowed}
        supers_remaining = set(
            User.objects.filter(is_superuser=True)
            .exclude(pk__in=allowed_ids)
            .values_list("pk", flat=True)
        )
        if not supers_remaining:
            kept = []
            for user in allowed:
                if user.is_superuser:
                    blocked.append((user, "не можна видалити останнього суперкористувача"))
                else:
                    kept.append(user)
            allowed = kept
        for user, reason in blocked:
            messages.warning(request, f"{user.username}: {reason}")
        if allowed:
            super().delete_queryset(request, queryset.filter(pk__in=[u.pk for u in allowed]))


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass


@admin.register(Wishlist)
class WishlistAdmin(ModelAdmin):
    list_display = ("user", "product", "created_at")
    autocomplete_fields = ["user", "product"]
    search_fields = ("user__username", "user__email", "product__name")
