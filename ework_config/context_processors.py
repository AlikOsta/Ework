from .utils import get_config

def site_config(request):
    """Контекстный процессор для предоставления конфигурации сайта в шаблоны"""
    config = get_config()
    
    return {
        'site_config': {
            'site_name': config.site_name,
            'site_description': config.site_description,
            'bot_username': config.bot_username,
            'telegram_channel': config.telegram_channel,
            'telegram_group': config.telegram_group,
            'contact_email': config.contact_email,
            'support_email': config.support_email,
            'meta_keywords': config.meta_keywords,
            'meta_description': config.meta_description,
            'maintenance_mode': config.maintenance_mode,
        }
    }
