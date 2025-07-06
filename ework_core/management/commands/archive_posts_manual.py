from django.core.management.base import BaseCommand
from ework_core.tasks import archive_expired_posts

class Command(BaseCommand):
    help = 'Ручная архивация истекших постов'

    def handle(self, *args, **options):
        self.stdout.write("Запуск ручной архивации истекших постов...")
        
        result = archive_expired_posts()
        
        if result['success']:
            self.stdout.write(
                self.style.SUCCESS(f'Архивация завершена: {result["message"]}')
            )
        else:
            self.stdout.write(
                self.style.ERROR(f'Ошибка архивации: {result["message"]}')
            )
        
        self.stdout.write(f"Архивировано постов: {result.get('archived_count', 0)}")
        
        return "Команда завершена"