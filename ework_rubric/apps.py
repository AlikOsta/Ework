from django.apps import AppConfig


class EworkRubricConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ework_rubric'

    def ready(self):
        import ework_rubric.translation

