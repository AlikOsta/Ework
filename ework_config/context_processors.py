from .utils import get_config

def site_config(request):
    """Контекстный процессор для предоставления конфигурации сайта в шаблоны"""
    config = get_config()
    
    return {
        'site_config': {
            'site_name': config.site_name,
            'site_description': config.site_description,
            'bot_username': config.bot_username,
            'admin_username': config.admin_username,
        }
    }
