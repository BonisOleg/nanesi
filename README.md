# NANESI — Beauty Store

Інтернет-магазин косметики на Django (Variant A: catalog · pricing · commerce · shipping · accounts · content · seo · integrations).

Візуальний макет (`_mockup/`) погоджений із замовником і не змінюється в рамках цього етапу.

## Стек

Python 3.12+ · Django 5.1 · PostgreSQL 16 · django-unfold (адмінка) · django-modeltranslation (uk/ru/en) · HTMX · Docker + nginx.

## Локальний запуск (Docker)

```bash
cp .env.example .env
docker compose up -d --build
docker compose exec backend python3 manage.py createsuperuser
```

Адмінка: http://localhost:8000/admin/

## Локальний запуск без Docker

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # і вкажіть POSTGRES_HOST=localhost або SQLite для dev
python3 manage.py migrate
python3 manage.py createsuperuser
python3 manage.py runserver
```

## Структура

```
config/         # налаштування Django (base/develop/production/test)
src/
  core/          # спільні абстракції (TimeStampedModel, SeoFieldsMixin, SingletonModel)
  accounts/      # User, роль, Wishlist
  catalog/       # Product, ProductVariant, Category, Brand, Supplier, Review, імпорт CSV/XLSX
  content/       # SiteSettings, StaticPage, BlogPost
deploy/          # Dockerfile + nginx конфіг
_mockup/         # погоджений frontend-макет (не редагується цим етапом)
```

## Етапи реалізації

Повний план — `.cursor/plans/nanesi_django_shop_build_408d3739.plan.md`. Поточний етап: **B — Django scaffold** (моделі, адмінка, імпорт постачальника). Кошик/checkout/оплата/НП — етап C.
