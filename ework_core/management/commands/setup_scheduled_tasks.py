"""
Простая команда для настройки периодических задач Django RQ
"""
from django.core.management.base import BaseCommand
from django_rq import get_scheduler


class Command(BaseCommand):
    help = 'Настройка периодических задач для архивирования постов'

    def add_arguments(self, parser):
        parser.add_argument('--setup', action='store_true', help='Создать периодические задачи')
        parser.add_argument('--clear', action='store_true', help='Удалить все задачи')

    def handle(self, *args, **options):
        if options['setup']:
            self.setup_tasks()
        elif options['clear']:
            self.clear_tasks()
        else:
            self.stdout.write('Используйте --setup или --clear')

    def setup_tasks(self):
        """Создать периодические задачи"""
        try:
            scheduler = get_scheduler('default')
            
            # Удаляем существующие задачи
            for job in scheduler.get_jobs():
                job.delete()
            
            # Создаем новые задачи
            jobs = [
                ('0 0 * * *', 'ework_core.tasks.archive_expired_posts', 'archive_posts'),
                ('0 1 * * *', 'ework_core.tasks.remove_expired_highlights', 'remove_highlights'), 
                ('0 2 * * *', 'ework_core.tasks.remove_expired_photo_addons', 'remove_photos'),
            ]
            
            for cron, func, job_id in jobs:
                job = scheduler.cron(cron, func=func)
                job.id = job_id
                job.save()
            
            self.stdout.write(self.style.SUCCESS('✅ Задачи настроены'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Ошибка: {e}'))

    def clear_tasks(self):
        """Удалить все задачи"""
        try:
            scheduler = get_scheduler('default')
            count = len(scheduler.get_jobs())
            
            for job in scheduler.get_jobs():
                job.delete()
            
            self.stdout.write(self.style.SUCCESS(f'🗑️ Удалено {count} задач'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Ошибка: {e}'))