from django.apps import AppConfig


class EworkCoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ework_core'

    def ready(self):
        try:
            import ework_core.signals
        except ImportError:
            # Если mistralai не установлен, пропускаем
            pass 
