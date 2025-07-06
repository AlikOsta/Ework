from django.db import migrations
from django.utils import timezone

def create_scheduled_tasks(apps, schema_editor):
    """Создание запланированных задач Django-Q"""
    try:
        from django_q.models import Schedule
        
        # Создаем задачу архивации истекших постов
        Schedule.objects.get_or_create(
            name='archive_expired_posts',
            defaults={
                'func': 'ework_core.tasks.archive_expired_posts',
                'schedule_type': Schedule.DAILY,
                'next_run': timezone.now().replace(hour=2, minute=0, second=0, microsecond=0),
                'repeats': -1,  # Бесконечное повторение
            }
        )
    except ImportError:
        # Django-Q может быть еще не установлено
        pass

def remove_scheduled_tasks(apps, schema_editor):
    """Удаление запланированных задач Django-Q"""
    try:
        from django_q.models import Schedule
        Schedule.objects.filter(name='archive_expired_posts').delete()
    except ImportError:
        pass

class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.RunPython(create_scheduled_tasks, remove_scheduled_tasks),
    ]
