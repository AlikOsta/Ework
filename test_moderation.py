#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ework.settings')
django.setup()

from ework_job.models import PostJob
from ework_locations.models import City
from ework_currency.models import Currency
from ework_rubric.models import SubRubric
from django.contrib.auth import get_user_model

User = get_user_model()

# Получаем объекты для создания поста
user = User.objects.get(id=2)
city = City.objects.first()
currency = Currency.objects.first()
sub_rubric = SubRubric.objects.first()

print("Создаем тестовый пост для проверки модерации...")

# Создаем пост для проверки модерации
post = PostJob.objects.create(
    title="Тестовая вакансия",
    description="Ищем программиста Python для работы с Django",
    price=50000,
    city=city,
    currency=currency,
    sub_rubric=sub_rubric,
    user=user,
    status=0  # На модерации
)

print(f"Пост создан с ID: {post.id}")
print(f"Статус: {post.status}")
print("Ожидаем результат модерации...")

import time
time.sleep(5)

# Проверяем статус после модерации
post.refresh_from_db()
print(f"Статус после модерации: {post.status}")

status_names = {0: 'Модерация', 1: 'Проверяется', 2: 'Отклонено', 3: 'Опубликовано'}
print(f"Расшифровка: {status_names.get(post.status, 'Неизвестно')}")
