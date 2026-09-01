from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("kabinet/", views.profile_view, name="profile"),
    path("kabinet/vkhid/", views.auth_view, name="login"),
    path("kabinet/vykhid/", views.logout_view, name="logout"),
    path("kabinet/zamovlennya/", views.order_list_view, name="order_list"),
    path("kabinet/zamovlennya/<str:order_number>/", views.order_detail_view, name="order_detail"),
    path("kabinet/zamovlennya/<str:order_number>/povtoryty/", views.order_repeat_view, name="order_repeat"),

    path("obrane/", views.wishlist_view, name="wishlist"),
    path("obrane/render/", views.wishlist_render_view, name="wishlist_render"),
    path("obrane/toggle/<int:product_id>/", views.wishlist_toggle_view, name="wishlist_toggle"),

    # Відновлення пароля — лише для акаунтів з email (SMS-провайдера в проєкті ще немає)
    path(
        "kabinet/vidnovlennya/",
        auth_views.PasswordResetView.as_view(
            template_name="accounts/password_reset.html",
            email_template_name="accounts/password_reset_email.html",
            subject_template_name="accounts/password_reset_subject.txt",
            success_url="/kabinet/vidnovlennya/nadislano/",
        ),
        name="password_reset",
    ),
    path(
        "kabinet/vidnovlennya/nadislano/",
        auth_views.PasswordResetDoneView.as_view(template_name="accounts/password_reset_done.html"),
        name="password_reset_done",
    ),
    path(
        "kabinet/vidnovlennya/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="accounts/password_reset_confirm.html",
            success_url="/kabinet/vidnovlennya/uspishno/",
        ),
        name="password_reset_confirm",
    ),
    path(
        "kabinet/vidnovlennya/uspishno/",
        auth_views.PasswordResetCompleteView.as_view(template_name="accounts/password_reset_complete.html"),
        name="password_reset_complete",
    ),
]
