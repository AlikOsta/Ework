from .models import SiteConfig, SystemLog
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)


def get_config():
    """Получить конфигурацию с кэшированием"""
    config = cache.get('site_config')
    if config is None:
        config = SiteConfig.get_config()
        cache.set('site_config', config, 300)  # Кэшируем на 5 минут
    return config


def log_system_event(level, message, module=None, user_id=None, extra_data=None):
    """Логирование системных событий"""
    try:
        SystemLog.objects.create(
            level=level,
            message=message,
            module=module,
            user_id=user_id,
            extra_data=extra_data
        )
    except Exception as e:
        logger.error(f"Ошибка записи в системный лог: {e}")


def clear_config_cache():
    """Очистить кэш конфигурации"""
    cache.delete('site_config')


# Сигнал для очистки кэша при изменении конфигурации
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

@receiver(post_save, sender=SiteConfig)
def clear_cache_on_config_save(sender, **kwargs):
    clear_config_cache()

@receiver(post_delete, sender=SiteConfig)
def clear_cache_on_config_delete(sender, **kwargs):
    clear_config_cache()
