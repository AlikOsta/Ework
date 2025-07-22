
from .utils import get_config

_bot_config = None

def get_bot_config():
    """Получить конфигурацию бота с кэшированием"""
    global _bot_config
    if _bot_config is None:
        config = get_config()
        _bot_config = {
            'bot_token': config.bot_token,
            'miniapp_url': config.site_url + '/users/index/',
            'payment_provider_token': config.payment_provider_token,
            'notification_bot_token': config.bot_token,
            'admin_chat_id': config.admin_chat_id,
        }
    return _bot_config

def clear_bot_config_cache():
    """Очистить кэш конфигурации бота"""
    global _bot_config
    _bot_config = None
