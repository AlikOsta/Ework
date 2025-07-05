"""
Команда для настройки периодических задач Django-Q
"""
from django.core.management.base import BaseCommand
from django_q.models import Schedule
from django_q.tasks import schedule


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
        
        # Удаляем существующие задачи с теми же именами
        Schedule.objects.filter(name__in=[
            'archive_expired_posts',
            'cleanup_old_tasks'
        ]).delete()
        
        # Создаем задачу архивирования постов (ежедневно в 00:00)
        schedule(
            'ework_core.tasks.archive_expired_posts',
            name='archive_expired_posts',
            schedule_type=Schedule.DAILY,
            next_run=None,  # Будет запланировано на следующую полночь
            repeats=-1  # Бесконечно
        )
        
        # Создаем задачу очистки старых задач (еженедельно)
        schedule(
            'ework_core.tasks.cleanup_old_tasks',
            name='cleanup_old_tasks',
            schedule_type=Schedule.WEEKLY,
            repeats=-1
        )
        
        self.stdout.write(
            self.style.SUCCESS('✅ Периодические задачи настроены:')
        )
        self.stdout.write('  - archive_expired_posts: ежедневно в 00:00')
        self.stdout.write('  - cleanup_old_tasks: еженедельно')

    def show_status(self):
        """Показать статус периодических задач"""
        schedules = Schedule.objects.all()
        
        if not schedules:
            self.stdout.write(
                self.style.WARNING('⚠️  Периодические задачи не настроены')
            )
            return
        
        self.stdout.write('📅 Статус периодических задач:')
        self.stdout.write('-' * 50)
        
        for schedule_obj in schedules:
            status = '✅ Активна' if schedule_obj.enabled else '❌ Отключена'
            next_run = schedule_obj.next_run.strftime('%Y-%m-%d %H:%M:%S') if schedule_obj.next_run else 'Не запланирована'
            
            self.stdout.write(f"Название: {schedule_obj.name}")
            self.stdout.write(f"Функция: {schedule_obj.func}")
            self.stdout.write(f"Статус: {status}")
            self.stdout.write(f"Тип: {schedule_obj.get_schedule_type_display()}")
            self.stdout.write(f"Следующий запуск: {next_run}")
            self.stdout.write('-' * 30)

    def remove_schedules(self):
        """Удалить все периодические задачи"""
        count = Schedule.objects.count()
        Schedule.objects.all().delete()
        
        self.stdout.write(
            self.style.SUCCESS(f'🗑️  Удалено {count} периодических задач')
        )