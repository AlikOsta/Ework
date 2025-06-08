from django.apps import AppConfig


class EworkCoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ework_core'

    def ready(self):
        import ework_core.signals 
