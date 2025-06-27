#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ework.settings')
django.setup()

from ework_premium.models import Payment
from django.contrib.auth import get_user_model

User = get_user_model()

# Проверяем платеж ID 30
try:
    payment = Payment.objects.get(id=30)
    print(f"Платеж 30 найден:")
    print(f"  ID: {payment.id}")
    print(f"  User: {payment.user.username} (ID: {payment.user.id})")
    print(f"  User telegram_id: {payment.user.telegram_id}")
    print(f"  Status: {payment.status}")
    print(f"  Order ID: {payment.order_id}")
    print(f"  Amount: {payment.amount}")
    print(f"  Post data exists: {bool(payment.post_data)}")
    
    # Проверяем условия поиска из кода
    print(f"\nПроверяем условия поиска:")
    print(f"  user__telegram_id=2: {payment.user.telegram_id == 2}")
    print(f"  status='pending': {payment.status == 'pending'}")
    
except Payment.DoesNotExist:
    print("❌ Платеж 30 не найден")
    
    # Показываем последние платежи
    print("\nПоследние платежи:")
    for p in Payment.objects.order_by('-id')[:5]:
        print(f"  ID: {p.id}, User: {p.user.username}, TG ID: {p.user.telegram_id}, Status: {p.status}")
