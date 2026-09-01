from django.urls import path

from . import views

app_name = "content"

urlpatterns = [
    # str, не slug: slugify(allow_unicode=True) дає кириличні слаги.
    path("blog/", views.BlogListView.as_view(), name="blog_list"),
    path("blog/<str:slug>/", views.BlogDetailView.as_view(), name="blog_detail"),
    path("newsletter/subscribe/", views.newsletter_subscribe, name="newsletter_subscribe"),
    # Catch-all одного сегмента (pro-nas/, dostavka-i-oplata/, oferta/, polityka-.../) —
    # МАЄ підключатись останнім у config/urls.py, інакше перехопить інші шляхи.
    path("<str:slug>/", views.PageDetailView.as_view(), name="page_detail"),
]
