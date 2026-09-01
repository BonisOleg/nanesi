from django.urls import path

from . import views

app_name = "commerce"

urlpatterns = [
    # Слаги — за картою сайту v4.1 (розділ 9 «Адреси»)
    path("koshyk/", views.CartView.as_view(), name="cart"),
    path("koshyk/add/<int:variant_id>/", views.cart_add, name="cart_add"),
    path("koshyk/update/<int:item_id>/", views.cart_update, name="cart_update"),
    path("koshyk/remove/<int:item_id>/", views.cart_remove, name="cart_remove"),
    path("koshyk/promo/apply/", views.promo_apply, name="promo_apply"),
    path("koshyk/promo/remove/", views.promo_remove, name="promo_remove"),
    path("oformlennya/", views.CheckoutView.as_view(), name="checkout"),
    path("dyakuyemo/<str:order_number>/", views.ThankYouView.as_view(), name="thank_you"),
    path("oformlennya/<str:order_number>/pay/", views.PaymentInitView.as_view(), name="payment_init"),
    path("oformlennya/<str:order_number>/pay/callback/", views.payment_callback, name="payment_callback"),
    path("payment/webhook/", views.payment_webhook, name="payment_webhook"),
]
