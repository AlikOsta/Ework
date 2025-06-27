#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ework.settings')
django.setup()

from ework_core.views import publish_post_after_payment
from ework_premium.models import Payment
from django.contrib.auth import get_user_model

User = get_user_model()

# Находим последний платеж с данными поста
payment = Payment.objects.filter(post_data__isnull=False).order_by('-id').first()

if payment:
    print(f"Тестируем платеж ID: {payment.id}")
    print(f"Пользователь: {payment.user.username} (ID: {payment.user.id})")
    print(f"Telegram ID: {payment.user.telegram_id}")
    print(f"Статус: {payment.status}")
    print(f"Данные поста: {bool(payment.post_data)}")
    
    if payment.user.telegram_id:
        print("\nВызываем publish_post_after_payment...")
        success = publish_post_after_payment(payment.user.telegram_id, payment.id)
        print(f"Результат: {success}")
        
        # Обновляем статус платежа
        payment.refresh_from_db()
        print(f"Новый статус платежа: {payment.status}")
    else:
        print("❌ У пользователя нет telegram_id")
else:
    print("❌ Не найдено платежей с данными поста")
