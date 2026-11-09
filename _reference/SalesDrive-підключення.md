# Підключення SalesDrive (Nanesi)

Код інтеграції вже готовий: після створення/зміни замовлення пишеться outbox і (якщо є ключі) одразу відправляється в CRM. Без ключів події лишаються `PENDING`.

## 1. Що взяти в кабінеті SalesDrive

1. Увійдіть у кабінет (URL вигляду `https://<акаунт>.salesdrive.me`).
2. **API URL** — базовий адрес акаунту без слеша в кінці, наприклад:
   `https://nanesi.salesdrive.me`
3. **API Key** — у налаштуваннях інтеграцій / API (розділ на кшталт «API», «Інтеграції», «Webhook»).
   Скопіюйте ключ для заголовка `X-Api-Key`.
4. **Webhook secret** — придумайте довгий випадковий рядок (або згенеруйте в кабінеті, якщо є поле секрету).
   Його сайт очікує в шляху URL, не в тілі запиту.

Якщо в кабінеті не видно API Key — увімкніть API/інтеграції в тарифі або попросіть підтримку SalesDrive відкрити доступ.

## 2. Поля в `.env` (прод і локально)

```env
SALESDRIVE_API_URL=https://nanesi.salesdrive.me
SALESDRIVE_API_KEY=ВАШ_КЛЮЧ
SALESDRIVE_WEBHOOK_SECRET=довгий-випадковий-секрет
```

Після змін — перезапуск gunicorn / docker compose.

## 3. Webhook у кабінеті SalesDrive → сайт

URL на сайті:

`https://nanesi.com.ua/webhooks/salesdrive/<SALESDRIVE_WEBHOOK_SECRET>/`

Метод: `POST`, подія: зміна статусу заявки (`status_change`).

Сайт оновлює статус замовлення за мапінгом у `src/commerce/salesdrive_mapper.py` і не шле зворотний CRM-апдейт (анти-цикл).

## 4. Що вже працює в коді

| Напрямок | Що відбувається |
|----------|-----------------|
| Сайт → SD | `ORDER_CREATED` / оновлення статусу / оплати / ТТН через outbox |
| Сайт → SD | Sync товарів: `python manage.py sync_salesdrive_products` |
| Черга | `python manage.py process_salesdrive_outbox` (якщо були PENDING) |
| SD → сайт | Webhook статусів |

Перевірка після ключів:

1. Зробіть тестове замовлення на сайті.
2. У адмінці замовлення з’явиться `salesdrive_order_id`.
3. У SalesDrive — нова заявка з позиціями, телефоном, доставкою.

Якщо outbox `FAILED` — дивіться логи / адмінку «Події інтеграції».
