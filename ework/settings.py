
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


SECRET_KEY = "dd"

DEBUG = True

ALLOWED_HOSTS = []

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
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
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

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'ework_user_tg.TelegramUser'

USE_I18N = True
USE_L10N = True 

LANGUAGES = [
    ('en', 'English'),
    ('ru', 'Russian'),
    ('uk', 'Ukrainian'),
]
# Путь(и) к каталогамimport os переводов
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale'),
]

ROSETTA_MESSAGES_PER_PAGE = 50
ROSETTA_ENABLE_TRANSLATION_SUGGESTIONS = True
ROSETTA_STORAGE_CLASS = 'rosetta.storage.CacheRosettaStorage'
ROSETTA_UWSGI_AUTO_RELOAD = True


STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]