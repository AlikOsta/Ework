# Система тарифов и оплаты

## Как работает система:

### 1. Тарифы:
- **Бесплатная публикация** (0 UAH) - 1 пост в неделю, без фото
- **Стандартный пост** (50 UAH) - обычный пост без фото
- **Пост с фото** (100 UAH) - пост с возможностью добавления фото
- **Премиум пост** (150 UAH) - пост с фото и цветным выделением

### 2. Логика выбора тарифа:
- Если пользователь не использовал бесплатный тариф на этой неделе - автоматически выбирается бесплатный
- Иначе выбирается первый платный тариф
- При выборе тарифа с фото показывается поле загрузки изображения
- Кнопка меняется: "Опубликовать" для бесплатного, "Оплатить XXX UAH" для платных

### 3. Процесс оплаты:
1. Пользователь заполняет форму и выбирает платный тариф
2. Создается запись Payment в базе данных
3. Через Telegram WebApp вызывается `window.Telegram.WebApp.openInvoice()`
4. После успешной оплаты Telegram бот отправляет уведомление на webhook
5. Система публикует пост на модерацию

### 4. API endpoints:

#### Webhook для уведомлений от бота:
```
POST /payments/webhook/simple/
Content-Type: application/json

{
    "payment_id": 123,
    "status": "paid" | "failed",
    "telegram_payment_charge_id": "xxx",
    "provider_payment_charge_id": "yyy"
}
```

#### Тестовый webhook:
```
POST /payments/webhook/test/
Content-Type: application/json

{
    "payment_id": 123
}
```

### 5. Интеграция с Telegram ботом:

В коде бота при получении successful_payment события:

```python
@bot.message_handler(content_types=['successful_payment'])
def successful_payment(message):
    payment_id = extract_payment_id_from_invoice_payload(message.successful_payment.invoice_payload)
    
    # Отправляем уведомление на webhook
    webhook_data = {
        'payment_id': payment_id,
        'status': 'paid',
        'telegram_payment_charge_id': message.successful_payment.telegram_payment_charge_id,
        'provider_payment_charge_id': message.successful_payment.provider_payment_charge_id
    }
    
    requests.post('https://yourdomain.com/payments/webhook/simple/', json=webhook_data)
```

### 6. Moderation:

Для обработки модерации используйте команду:
```bash
python manage.py process_moderation --auto-approve  # одобрить все посты
python manage.py process_moderation                 # показать посты на модерации
python manage.py process_moderation --post-id 123 --action approve  # одобрить конкретный пост
python manage.py process_moderation --post-id 123 --action reject   # отклонить пост
```

### 7. Тестирование:

1. Создайте пост с бесплатным тарифом - должен сразу публиковаться
2. Создайте пост с платным тарифом - должен создаваться Payment
3. Используйте тестовый webhook для имитации оплаты
4. Проверьте что пост появился на модерации
5. Одобрите пост через команду process_moderation

### 8. Файлы системы:

- `/app/ework_payment/services.py` - основная логика платежей
- `/app/ework_payment/simple_webhook.py` - простой webhook для уведомлений
- `/app/ework_post/forms.py` - форма с выбором тарифов
- `/app/ework_core/management/commands/process_moderation.py` - команда модерации
- Шаблоны форм в `/app/ework_job/templates/` и `/app/ework_services/templates/`

### 9. Что настроить:

1. В `ework_post/views.py` строка 81 - замените URL бота на реальный
2. Добавьте настройки Telegram Payments в settings.py
3. Настройте webhook URL в боте
4. Добавьте обработку платежей в код бота