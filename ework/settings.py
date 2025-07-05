
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


SECRET_KEY = "dd"

DEBUG = True

ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '*',  # Для разработки - в продакшене нужно указать конкретные домены
]

CSRF_COOKIE_DOMAIN = None  # Убираем ограничение домена
CSRF_COOKIE_SECURE = True  # Для HTTPS
CSRF_COOKIE_HTTPONLY = False  # Важно! Позволяет JS доступ к cookie
CSRF_COOKIE_SAMESITE = None  # Убираем SameSite ограничения
CSRF_USE_SESSIONS = True  # Используем сессии вместо cookie
CSRF_COOKIE_AGE = None

CSRF_TRUSTED_ORIGINS = [
    'https://*.ngrok-free.app',  # Для ngrok в разработке
]

# Настройки сессий для Telegram Mini App
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = False
SESSION_COOKIE_SAMESITE = None
SESSION_SAVE_EVERY_REQUEST = True

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rosetta',  
    'django_htmx',  
    'widget_tweaks',  
    'polymorphic',  
    'django_q',  # Django Q для фоновых задач
    'ework_bot_tg', #бот ТГ и его фунционнал
    'ework_user_tg', # модель пользователя и авторизация
    'ework_job', # объявления о работе 
    'ework_post', # абмтрактная модель постов 
    'ework_services', # объявления о услугах
    'ework_locations', # города 
    'ework_premium', # модели для премиум объявления
    'ework_rubric', # рубрики объявлений
    'ework_payment', # оплата
    'ework_currency', # валюты
    'ework_core', # ядро
    'ework_config', # конфигурация
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',  
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'ework_user_tg.middleware.UserLanguageMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_htmx.middleware.HtmxMiddleware',
]

ROOT_URLCONF = 'ework.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'ework_rubric.middleware.post_rubric_context_processor',
                'ework_config.context_processors.site_config',
            ],
        },
    },
]

WSGI_APPLICATION = 'ework.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'ru'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'ework_user_tg.TelegramUser'

USE_L10N = True 

LANGUAGES = [
    ('ru', 'Russian'),
    ('uk', 'Ukrainian'),
]


LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

BASE_DIR = os.path.dirname(os.path.dirname(__file__))


ROSETTA_MESSAGES_PER_PAGE = 50
ROSETTA_ENABLE_TRANSLATION_SUGGESTIONS = True
ROSETTA_STORAGE_CLASS = 'rosetta.storage.CacheRosettaStorage'
ROSETTA_UWSGI_AUTO_RELOAD = True


STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
    os.path.join(BASE_DIR, 'ework_core', 'static'),
]