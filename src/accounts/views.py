"""Thin views: parse -> selector/service -> render (ecommerce_business_logic_skill, rule 3)."""
from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_GET, require_POST

from src.accounts import selectors, services
from src.accounts.forms import LoginForm, ProfileForm, RegisterForm, SavedWarehouseForm
from src.catalog.models import Product


def _parse_ids(raw: str) -> list[int]:
    ids: list[int] = []
    for chunk in (raw or "").split(","):
        chunk = chunk.strip()
        if chunk.isdigit():
            ids.append(int(chunk))
    return ids


def auth_view(request):
    """Одна сторінка вхід/реєстрація (Відповіді п.6) — перемикання вкладками, без переходу."""
    if request.user.is_authenticated:
        return redirect("accounts:profile")

    next_url = request.GET.get("next") or request.POST.get("next") or reverse("accounts:profile")
    active_tab = "login"
    login_form = LoginForm(request)
    register_form = RegisterForm()

    if request.method == "POST":
        active_tab = request.POST.get("form", "login")
        wishlist_ids = _parse_ids(request.POST.get("wishlist_ids", ""))

        if active_tab == "register":
            register_form = RegisterForm(request.POST)
            if register_form.is_valid():
                user = register_form.save()
                auth_login(request, user, backend="src.accounts.backends.PhoneOrEmailBackend")
                services.sync_guest_wishlist(user, wishlist_ids)
                messages.success(request, _("Вітаємо! Акаунт створено."))
                return redirect(next_url)
        else:
            login_form = LoginForm(request, data=request.POST)
            if login_form.is_valid():
                user = login_form.get_user()
                auth_login(request, user)
                services.sync_guest_wishlist(user, wishlist_ids)
                messages.success(request, _("Ви увійшли в кабінет."))
                return redirect(next_url)

    return render(request, "accounts/auth.html", {
        "login_form": login_form,
        "register_form": register_form,
        "active_tab": active_tab,
        "next": next_url,
    })


@require_POST
def logout_view(request):
    auth_logout(request)
    messages.info(request, _("Ви вийшли з кабінету."))
    return redirect("catalog:home")


@login_required
def profile_view(request):
    profile_form = ProfileForm(instance=request.user)
    warehouse_form = SavedWarehouseForm(instance=request.user)

    if request.method == "POST":
        which = request.POST.get("form")
        if which == "warehouse":
            warehouse_form = SavedWarehouseForm(request.POST, instance=request.user)
            if warehouse_form.is_valid():
                warehouse_form.save()
                messages.success(request, _("Відділення збережено."))
                return redirect("accounts:profile")
        else:
            profile_form = ProfileForm(request.POST, instance=request.user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, _("Дані профілю оновлено."))
                return redirect("accounts:profile")

    return render(request, "accounts/profile.html", {
        "profile_form": profile_form,
        "warehouse_form": warehouse_form,
        "recent_orders": selectors.user_orders(request.user)[:3],
        "wishlist_count": request.user.wishlist_items.count(),
    })


@login_required
def order_list_view(request):
    orders = selectors.user_orders(request.user)
    page = Paginator(orders, 10).get_page(request.GET.get("page"))
    return render(request, "accounts/order_list.html", {"page_obj": page})


@login_required
def order_detail_view(request, order_number: str):
    order = selectors.user_order_detail(request.user, order_number)
    if order is None:
        messages.error(request, _("Замовлення не знайдено"))
        return redirect("accounts:order_list")
    return render(request, "accounts/order_detail.html", {"order": order})


@login_required
@require_POST
def order_repeat_view(request, order_number: str):
    order = selectors.user_order_detail(request.user, order_number)
    if order is None:
        messages.error(request, _("Замовлення не знайдено"))
        return redirect("accounts:order_list")

    added, unavailable = services.repeat_order(request, order)
    if added:
        messages.success(
            request,
            _("Додано в кошик %(added)s позицій із замовлення №%(number)s.")
            % {"added": added, "number": order.number},
        )
    if unavailable:
        messages.warning(request, _("Немає в наявності: ") + ", ".join(unavailable))
    if not added and not unavailable:
        messages.info(request, _("У цьому замовленні немає товарів для повторення."))
    return redirect("commerce:cart")


def wishlist_view(request):
    context = {}
    if request.user.is_authenticated:
        context["products"] = list(selectors.wishlist_products(request.user))
    return render(request, "accounts/wishlist.html", context)


@require_GET
def wishlist_render_view(request):
    """Для гостя: рендер карток товарів за id з localStorage (JS fetch на /obrane/)."""
    ids = _parse_ids(request.GET.get("ids", ""))
    products = []
    if ids:
        from src.catalog.selectors import visible_products

        products = list(visible_products().filter(pk__in=ids))
    return render(request, "accounts/partials/_wishlist_grid.html", {"products": products})


@login_required
@require_POST
def wishlist_toggle_view(request, product_id: int):
    get_object_or_404(Product, pk=product_id, is_active=True)
    active = services.toggle_wishlist(request.user, product_id)
    if request.headers.get("X-Requested-With") == "fetch":
        return JsonResponse({"active": active, "count": request.user.wishlist_items.count()})
    return redirect(request.META.get("HTTP_REFERER") or "accounts:wishlist")
