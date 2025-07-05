"""
Команда для настройки периодических задач Django RQ
"""
from django.core.management.base import BaseCommand
from django_rq import get_scheduler
import django_rq


class Command(BaseCommand):
    help = 'Настройка периодических задач для архивирования постов'

    def add_arguments(self, parser):
        parser.add_argument(
            '--setup',
            action='store_true',
            help='Создать/обновить периодические задачи',
        )
        parser.add_argument(
            '--status',
            action='store_true',
            help='Показать статус периодических задач',
        )
        parser.add_argument(
            '--remove',
            action='store_true',
            help='Удалить все периодические задачи',
        )

    def handle(self, *args, **options):
        if options['setup']:
            self.setup_schedules()
        elif options['status']:
            self.show_status()
        elif options['remove']:
            self.remove_schedules()
        else:
            self.stdout.write('Используйте --setup, --status или --remove')

    def setup_schedules(self):
        """Создать или обновить периодические задачи"""
        self.stdout.write('Настройка периодических задач...')
        
        try:
            scheduler = get_scheduler('default')
            
            # Удаляем существующие задачи с теми же именами
            for job in scheduler.get_jobs():
                if job.id in ['archive_expired_posts']:
                    job.delete()
            
            # Создаем задачу архивирования постов (ежедневно в 00:00)
            scheduler.cron(
                '0 0 * * *',  # cron expression для ежедневного запуска в 00:00
                func='ework_core.tasks.archive_expired_posts',
                id='archive_expired_posts',
                replace_existing=True
            )
            
            self.stdout.write(
                self.style.SUCCESS('✅ Периодические задачи настроены:')
            )
            self.stdout.write('  - archive_expired_posts: ежедневно в 00:00')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Ошибка настройки задач: {e}')
            )

    def show_status(self):
        """Показать статус периодических задач"""
        try:
            scheduler = get_scheduler('default')
            jobs = scheduler.get_jobs()
            
            if not jobs:
                self.stdout.write(
                    self.style.WARNING('⚠️  Периодические задачи не настроены')
                )
                return
            
            self.stdout.write('📅 Статус периодических задач:')
            self.stdout.write('-' * 50)
            
            for job in jobs:
                self.stdout.write(f"ID: {job.id}")
                self.stdout.write(f"Функция: {job.func_name}")
                self.stdout.write(f"Следующий запуск: {job.get_next_run_time()}")
                self.stdout.write('-' * 30)
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Ошибка получения статуса: {e}')
            )

    def remove_schedules(self):
        """Удалить все периодические задачи"""
        try:
            scheduler = get_scheduler('default')
            jobs = scheduler.get_jobs()
            count = len(jobs)
            
            for job in jobs:
                job.delete()
            
            self.stdout.write(
                self.style.SUCCESS(f'🗑️  Удалено {count} периодических задач')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Ошибка удаления задач: {e}')
            )