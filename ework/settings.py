
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.getenv('SECRET_KEY')
DEBUG = True
ALLOWED_HOSTS = [
    'localhost',
    '46.254.107.43',
    'helpwork.com.ua',
    '127.0.0.1',
]
CSRF_COOKIE_DOMAIN = None  
CSRF_COOKIE_SECURE = True  
CSRF_COOKIE_HTTPONLY = False  
CSRF_COOKIE_SAMESITE = None  
CSRF_USE_SESSIONS = True  
CSRF_COOKIE_AGE = None
CSRF_TRUSTED_ORIGINS = [
    'https://helpwork.com.ua',
]
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = False
SESSION_COOKIE_SAMESITE = None
SESSION_SAVE_EVERY_REQUEST = True
INSTALLED_APPS = [
    'jazzmin',
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
    'django_q',  # Django-Q для фоновых задач
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
    'ework_stats', # статистика
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
STATIC_URL = '/static/'
STATIC_ROOT = '/home/HelpWork/Ework/staticfiles'
STATICFILES_DIRS = [
    '/home/HelpWork/Ework/static',
]
MEDIA_URL = '/media/'
MEDIA_ROOT = '/home/HelpWork/Ework/media'
Q_CLUSTER = {
    'name': 'ework_cluster',
    'workers': 2,
    'timeout': 30,
    'retry': 60,
    'queue_limit': 50,
    'bulk': 10,
    'orm': 'default',
    'catch_up': True,
    'save_limit': 250,
    'ack_failures': True,
    'max_attempts': 1,
    'attempt_count': 1,
    'cached': 60,
    'sync': False,
    'compress': True,
    'cpu_affinity': 1,
    'daemonize_workers': False,
    'log_level': 'INFO',
    'label': 'Django-Q',
    'redis': None,
    'schedule': {
        'collect_daily_stats': {
            'func': 'ework_stats.tasks.collect_daily_stats',
            'schedule_type': 'D',  
            'hour': 1,  
            'minute': 0
        },
    }
}  

JAZZMIN_SETTINGS = {
    "site_title": "Help Work Admin",
    "site_header": "Help Work",
    "site_brand": "Help Work",
    "site_url": "/",
    "copyright": "Help Work © 2025",
    "user_avatar": None,
    "topmenu_links": [
        {"name": "Главная", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "Перейти на сайт", "url": "/", "new_window": True},
        {"app": "ework_post"},
    ],
    "show_sidebar": True,
    "navigation_expanded": True,
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "ework_post.abspost": "fas fa-newspaper",
        "ework_post.postjob": "fas fa-briefcase",
        "ework_post.postservices": "fas fa-tools",
        "ework_config.siteconfig": "fas fa-cogs",
        "ework_config.subrubric": "fas fa-list",
        "ework_config.superrubric": "fas fa-folder",
        "ework_config.city": "fas fa-city",
        "ework_config.currency": "fas fa-money-bill",
        "ework_premium.package": "fas fa-box",
        "ework_premium.payment": "fas fa-credit-card",
        "ework_user_tg.telegramuser": "fab fa-telegram",
    },
    "order_with_respect_to": [
        "auth",
        "ework_user_tg",
        "ework_post",
        "ework_job",
        "ework_services",
        "ework_premium",
        "ework_config",
    ],
    "related_modal_active": True,
    "custom_css": None,
    "custom_js": None,
    "use_google_fonts_cdn": True,
    "show_ui_builder": True,
}
JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-primary",
    "accent": "accent-primary",
    "navbar": "navbar-dark",
    "no_navbar_border": False,
    "navbar_fixed": True,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-primary",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": True,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme": "default",
    "dark_mode_theme": None,
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success"
    }
}
