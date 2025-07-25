from .utils import get_config

def site_config(request):
    """Контекстный процессор для предоставления конфигурации сайта в шаблоны"""
    config = get_config()
    
    return {
        'site_config': {
            'bot_username': config.bot_username,
            'admin_telegram': config.admin_username if config else '@admin'
        }
    }
