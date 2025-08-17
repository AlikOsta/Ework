
import asyncio
from django.core.management.base import BaseCommand
from ework_bot_tg.bot import main

class Command(BaseCommand):
    help = 'Запускает Telegram бота'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Запуск Telegram бота...'))
        try:
            asyncio.run(main())
            return 0
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ошибка при запуске бота: {e}'))
            return 1
