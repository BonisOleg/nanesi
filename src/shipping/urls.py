from django.urls import path

from . import views

app_name = "shipping"

urlpatterns = [
    path("np/cities/", views.np_cities, name="np_cities"),
    path("np/warehouses/", views.np_warehouses, name="np_warehouses"),
]
