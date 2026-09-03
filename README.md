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

## Деплой на тестовий Droplet (HTTP + IP, без git)

Канон: `django-droplet-http-first`. Remote з’явиться пізніше — зараз код через rsync.

1. **Mac → сервер (код)** після появи IP і SSH:
   ```bash
   ./deploy/docker/rsync-up.sh root@DROPLET_IP
   # або SSH Host alias: ./deploy/docker/rsync-up.sh malyar
   ```
2. **На сервері:**
   ```bash
   cd /var/www/malyar
   cp .env.docker.example .env && nano .env   # SECRET_KEY, POSTGRES_PASSWORD, реальний IP замість DROPLET_IP
   bash deploy/docker/install-docker.sh
   bash deploy/docker/deploy.sh
   curl -sI -H "Host: <IP>" http://127.0.0.1/ | head -5
   ```
3. **Тестові дані (локальна БД + media):**
   ```bash
   ./deploy/docker/sync-data.sh push root@DROPLET_IP:/var/www/malyar --yes
   ```
   Dump уже містить users — `createsuperuser` лише якщо потрібен новий адмін **після** import.

Коли буде GitHub: `git clone` у `/var/www/malyar` замість rsync; оновлення — `git pull` + `bash deploy/docker/deploy.sh` (push ≠ live).

## Етапи реалізації

Повний план — `.cursor/plans/nanesi_django_shop_build_408d3739.plan.md`. Поточний етап: вітрина + підготовка DO HTTP-деплою.
