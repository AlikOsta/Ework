from django.core.management.base import BaseCommand
from django_q.models import Schedule
from django.utils import timezone

class Command(BaseCommand):
    help = 'Настройка регулярных задач Django-Q'

    def handle(self, *args, **options):
        # Создаем или обновляем задачу архивации истекших постов
        schedule, created = Schedule.objects.get_or_create(
            name='archive_expired_posts',
            defaults={
                'func': 'ework_core.tasks.archive_expired_posts',
                'schedule_type': Schedule.DAILY,
                'next_run': timezone.now().replace(hour=2, minute=0, second=0, microsecond=0),
                'repeats': -1,  # Бесконечное повторение
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Создана задача архивации постов: {schedule.name}')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'Задача архивации постов уже существует: {schedule.name}')
            )
        
        # Создаем задачу очистки старых задач Django-Q
        cleanup_schedule, cleanup_created = Schedule.objects.get_or_create(
            name='cleanup_old_tasks',
            defaults={
                'func': 'ework_core.tasks.cleanup_old_tasks',
                'schedule_type': Schedule.WEEKLY,
                'next_run': timezone.now().replace(hour=3, minute=0, second=0, microsecond=0),
                'repeats': -1,  # Бесконечное повторение
            }
        )
        
        if cleanup_created:
            self.stdout.write(
                self.style.SUCCESS(f'Создана задача очистки: {cleanup_schedule.name}')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'Задача очистки уже существует: {cleanup_schedule.name}')
            )
        
        self.stdout.write(self.style.SUCCESS('Настройка задач завершена'))