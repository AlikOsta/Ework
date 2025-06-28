from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from ework_config.models import AdminUser, SiteConfig


class Command(BaseCommand):
    help = 'Создание суперпользователя и настройка первичной конфигурации'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='Username для суперпользователя')
        parser.add_argument('--email', type=str, help='Email для суперпользователя')
        parser.add_argument('--telegram-id', type=int, help='Telegram ID администратора')

    def handle(self, *args, **options):
        User = get_user_model()
        
        username = options['username'] or 'admin'
        email = options['email'] or 'admin@ework.com'
        telegram_id = options['telegram_id'] or 123456789
        
        # Создаем суперпользователя если его нет
        if not User.objects.filter(username=username).exists():
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password='admin123',  # В продакшене поменять!
                telegram_id=telegram_id
            )
            self.stdout.write(
                self.style.SUCCESS(f'✅ Суперпользователь {username} создан')
            )
            self.stdout.write(f'   Email: {email}')
            self.stdout.write(f'   Password: admin123')
            self.stdout.write(f'   Telegram ID: {telegram_id}')
            
            # Создаем запись в AdminUser
            admin_user, created = AdminUser.objects.get_or_create(
                telegram_id=telegram_id,
                defaults={
                    'username': username,
                    'first_name': 'Admin',
                    'can_moderate_posts': True,
                    'can_manage_users': True,
                    'can_manage_payments': True,
                    'can_view_analytics': True,
                    'can_manage_config': True,
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS('✅ Запись в AdminUser создана')
                )
        else:
            self.stdout.write(
                self.style.WARNING(f'⚠️  Пользователь {username} уже существует')
            )
        
        # Проверяем/создаем конфигурацию
        config, created = SiteConfig.objects.get_or_create(pk=1)
        if created:
            self.stdout.write(
                self.style.SUCCESS('✅ Базовая конфигурация создана')
            )
        
        self.stdout.write('\n🚀 Теперь вы можете:')
        self.stdout.write('   1. Запустить сервер: python manage.py runserver')
        self.stdout.write('   2. Открыть админ панель: http://localhost:8000/admin/')
        self.stdout.write('   3. Настроить конфигурацию в разделе "Конфигурация сайта"')
