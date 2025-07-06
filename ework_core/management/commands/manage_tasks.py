from django.core.management.base import BaseCommand
from django_q.models import Schedule, Task
from django_q.tasks import async_task
from ework_config.models import SiteConfig

class Command(BaseCommand):
    help = 'Управление задачами Django-Q'

    def add_arguments(self, parser):
        parser.add_argument(
            '--action',
            choices=['status', 'run', 'schedule', 'history', 'config'],
            default='status',
            help='Действие для выполнения',
        )
        parser.add_argument(
            '--days',
            type=int,
            help='Установить срок жизни постов (в днях)',
        )

    def handle(self, *args, **options):
        action = options['action']
        
        if action == 'status':
            self.show_status()
        elif action == 'run':
            self.run_task()
        elif action == 'schedule':
            self.show_schedule()
        elif action == 'history':
            self.show_history()
        elif action == 'config':
            if options['days']:
                self.set_config(options['days'])
            else:
                self.show_config()

    def show_status(self):
        """Показать общий статус"""
        config = SiteConfig.get_config()
        self.stdout.write(self.style.SUCCESS('=== Статус Django-Q ==='))
        self.stdout.write(f'Срок жизни постов: {config.post_expiry_days} дней')
        
        # Запланированные задачи
        schedules = Schedule.objects.all()
        self.stdout.write(f'\nЗапланированных задач: {schedules.count()}')
        for schedule in schedules:
            self.stdout.write(f'  - {schedule.name}: {schedule.next_run}')
        
        # Последние выполненные задачи
        recent_tasks = Task.objects.filter(
            func='ework_core.tasks.archive_expired_posts'
        ).order_by('-started')[:3]
        
        self.stdout.write(f'\nПоследние выполнения архивации:')
        for task in recent_tasks:
            status = "✅ Успешно" if task.success else "❌ Ошибка"
            self.stdout.write(f'  - {task.started}: {status}')
            if task.result:
                self.stdout.write(f'    Результат: {task.result}')

    def run_task(self):
        """Запустить задачу архивации вручную"""
        self.stdout.write("Запуск задачи архивации...")
        task_id = async_task('ework_core.tasks.archive_expired_posts')
        self.stdout.write(self.style.SUCCESS(f'Задача поставлена в очередь: {task_id}'))

    def show_schedule(self):
        """Показать расписание задач"""
        schedules = Schedule.objects.all()
        self.stdout.write(self.style.SUCCESS('=== Расписание задач ==='))
        for schedule in schedules:
            self.stdout.write(f'Название: {schedule.name}')
            self.stdout.write(f'Функция: {schedule.func}')
            self.stdout.write(f'Тип: {schedule.get_schedule_type_display()}')
            self.stdout.write(f'Следующий запуск: {schedule.next_run}')
            self.stdout.write(f'Повторы: {schedule.repeats}')
            self.stdout.write('---')

    def show_history(self):
        """Показать историю выполнения"""
        tasks = Task.objects.filter(
            func='ework_core.tasks.archive_expired_posts'
        ).order_by('-started')[:10]
        
        self.stdout.write(self.style.SUCCESS('=== История выполнения задач ==='))
        for task in tasks:
            status = "✅ Успешно" if task.success else "❌ Ошибка"
            self.stdout.write(f'{task.started}: {status}')
            if task.result:
                self.stdout.write(f'  Результат: {task.result}')

    def show_config(self):
        """Показать конфигурацию"""
        config = SiteConfig.get_config()
        self.stdout.write(self.style.SUCCESS('=== Конфигурация ==='))
        self.stdout.write(f'Срок жизни постов: {config.post_expiry_days} дней')
        self.stdout.write(f'Сайт: {config.site_name}')
        self.stdout.write(f'URL: {config.site_url}')

    def set_config(self, days):
        """Установить срок жизни постов"""
        config = SiteConfig.get_config()
        old_days = config.post_expiry_days
        config.post_expiry_days = days
        config.save()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Срок жизни постов изменен: {old_days} → {days} дней'
            )
        )