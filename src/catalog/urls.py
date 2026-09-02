from django.urls import path

from . import views

app_name = "catalog"

urlpatterns = [
    # str, не slug: slugify(allow_unicode=True) дає кириличні слаги (Cyrillic),
    # а вбудований `slug`-конвертер Django приймає лише ASCII [-a-zA-Z0-9_]+.
    path("", views.home, name="home"),
    path("katalog/", views.catalog_list, name="catalog"),
    path("katalog/<str:category_slug>/", views.catalog_list, name="category_detail"),
    path("brendy/", views.brand_list, name="brand_list"),
    path("brendy/<str:brand_slug>/", views.catalog_list, name="brand_detail"),
    path("dobirka/<str:slug>/", views.collection_detail, name="collection_detail"),
    path("tovar/<str:slug>/", views.product_detail, name="product_detail"),
    path("tovar/<str:slug>/vidguk/", views.review_create, name="review_create"),
    path("poshuk/", views.catalog_list, name="search"),
]
