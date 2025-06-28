from django.core.management.base import BaseCommand
from ework_config.models import SiteConfig


class Command(BaseCommand):
    help = 'Инициализация конфигурации сайта с базовыми значениями'

    def handle(self, *args, **options):
        config, created = SiteConfig.objects.get_or_create(pk=1)
        
        if created:
            # Устанавливаем базовые значения для новой конфигурации
            config.site_name = 'eWork'
            config.site_description = 'Платформа для поиска работы и услуг'
            config.site_url = 'https://localhost:8000'
            config.bot_username = 'your_bot_username'
            config.contact_email = 'contact@ework.com'
            config.support_email = 'support@ework.com'
            config.meta_description = 'Найдите работу или предложите свои услуги на eWork'
            config.save()
            
            self.stdout.write(
                self.style.SUCCESS('✅ Конфигурация успешно создана с базовыми значениями')
            )
            self.stdout.write('⚠️  Не забудьте настроить:')
            self.stdout.write('   - Bot Token')
            self.stdout.write('   - Payment Provider Token')
            self.stdout.write('   - Mistral API Key')
            self.stdout.write('   - Notification Bot Token и Admin Chat ID')
            self.stdout.write('   - Bot Username')
        else:
            self.stdout.write(
                self.style.WARNING('⚠️  Конфигурация уже существует')
            )
