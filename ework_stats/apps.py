from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class EworkStatsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ework_stats'
    verbose_name = _('Статистика сайта')
