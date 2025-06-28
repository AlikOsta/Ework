# eWork Project - Agent Documentation

## Основные команды

### Разработка
- `python manage.py runserver` - запуск dev сервера
- `python manage.py check` - проверка проекта
- `python manage.py migrate` - применение миграций
- `python manage.py makemigrations` - создание миграций
- `python manage.py collectstatic` - сбор статических файлов

### Тестирование  
- `python manage.py test` - запуск тестов
- `python test_moderation.py` - тест модерации
- `python test_payment_processing.py` - тест платежей

## Структура проекта

### Основные приложения:
- `ework_core` - ядро системы, основные views и URL
- `ework_post` - абстрактная модель постов (AbsPost)
- `ework_job` - объявления о работе (PostJob extends AbsPost)
- `ework_services` - объявления об услугах (PostServices extends AbsPost)
- `ework_user_tg` - пользователи Telegram, авторизация, рейтинги
- `ework_payment` - система платежей
- `ework_locations` - города
- `ework_rubric` - рубрики объявлений
- `ework_currency` - валюты

### Ключевые модели:
- `AbsPost` - базовая модель объявления (polymorphic)
- `TelegramUser` - модель пользователя
- `UserRating` - система отзывов пользователей (1-5 звезд)
- `PostView` - просмотры объявлений
- `Favorite` - избранные объявления

### Шаблоны:
- `components/unified_card.html` - унифицированная карточка объявления
- `components/card.html` - основной список объявлений
- `includes/post_detail.html` - детальный просмотр объявления
- `user_ework/author_profile.html` - профиль пользователя
- `user_ework/rating_form.html` - форма отзыва

## Последние улучшения

### Оптимизация БД:
- Добавлены `select_related()` и `prefetch_related()` в queryset
- Кэширование рубрик в middleware
- Фильтрация только активных объектов

### Система отзывов:
- Интерактивная форма с визуальными звездами
- Ограничение: один отзыв на пользователя
- Отображение рейтинга в карточках и профилях

### Унификация UI:
- Создана единая карточка объявления для всех разделов
- Добавлены кликабельные ссылки на профили продавцов
- Кнопка "Оставить отзыв" в детальном просмотре

### Навигация:
- Клик по блоку продавца → переход в профиль
- В профиле: кнопки "Связаться" и "Оставить отзыв"
- Показ активных объявлений пользователя

## Технологии
- Django 4.x
- SQLite (dev)
- HTMX для динамических обновлений
- Bootstrap 5 + Material Icons
- Polymorphic для наследования моделей
- Telegram Mini App интеграция

## Настройки безопасности
- CSRF защита настроена для Telegram Mini App
- Middleware для проверки Telegram данных
- Мягкое удаление постов (soft delete)
