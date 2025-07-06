"""
Простая команда для ручного архивирования постов
"""
from django.core.management.base import BaseCommand
from ework_core.tasks import archive_expired_posts, get_expiry_stats


class Command(BaseCommand):
    help = 'Ручное архивирование истекших постов'

    def add_arguments(self, parser):
        parser.add_argument('--run', action='store_true', help='Запустить архивирование')
        parser.add_argument('--stats', action='store_true', help='Показать статистику')

    def handle(self, *args, **options):
        if options['stats']:
            self.show_stats()
        elif options['run']:
            self.run_archive()
        else:
            self.stdout.write('Используйте --run или --stats')

    def show_stats(self):
        """Показать статистику"""
        stats = get_expiry_stats()
        
        if 'error' in stats:
            self.stdout.write(self.style.ERROR(f'❌ Ошибка: {stats["error"]}'))
            return
        
        self.stdout.write('📊 Статистика постов:')
        self.stdout.write(f'Истекшие: {stats["expired_posts"]}')
        self.stdout.write(f'Истекают скоро: {stats["expiring_soon"]}')
        self.stdout.write(f'Срок: {stats["expiry_days"]} дней')

    def run_archive(self):
        """Запустить архивирование"""
        result = archive_expired_posts()
        
        if result['success']:
            self.stdout.write(
                self.style.SUCCESS(f'✅ Архивировано: {result["archived_count"]} постов')
            )
        else:
            self.stdout.write(
                self.style.ERROR(f'❌ Ошибка: {result["error"]}')
            )