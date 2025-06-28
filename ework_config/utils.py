from .models import SiteConfig
from django.core.cache import cache
import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

logger = logging.getLogger(__name__)

def get_config():
    """Получить конфигурацию с кэшированием"""
    config = cache.get('site_config')
    if config is None:
        config = SiteConfig.get_config()
        cache.set('site_config', config, 300) 
    return config

def clear_config_cache():
    """Очистить кэш конфигурации"""
    cache.delete('site_config')

@receiver(post_save, sender=SiteConfig)
def clear_cache_on_config_save(sender, **kwargs):
    clear_config_cache()

@receiver(post_delete, sender=SiteConfig)
def clear_cache_on_config_delete(sender, **kwargs):
    clear_config_cache()
