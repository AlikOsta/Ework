"""
Команда для ручного архивирования истекших постов
"""
from django.core.management.base import BaseCommand
from ework_core.tasks import archive_expired_posts, get_expiry_stats


class Command(BaseCommand):
    help = 'Ручное архивирование истекших постов'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Показать какие посты будут архивированы, но не архивировать их',
        )
        parser.add_argument(
            '--stats',
            action='store_true',
            help='Показать статистику по истекающим постам',
        )

    def handle(self, *args, **options):
        if options['stats']:
            self.show_stats()
        elif options['dry_run']:
            self.dry_run()
        else:
            self.archive_posts()

    def show_stats(self):
        """Показать статистику по истекающим постам"""
        self.stdout.write('📊 Статистика по истекающим постам:')
        self.stdout.write('-' * 40)
        
        stats = get_expiry_stats()
        
        if 'error' in stats:
            self.stdout.write(
                self.style.ERROR(f'❌ Ошибка: {stats["error"]}')
            )
            return
        
        self.stdout.write(f'Истекшие посты: {stats["expired_posts"]}')
        self.stdout.write(f'Истекают в ближайшие 3 дня: {stats["expiring_soon"]}')
        self.stdout.write(f'Срок хранения: {stats["expiry_days"]} дней')

    def dry_run(self):
        """Показать какие посты будут архивированы"""
        from django.utils import timezone
        from datetime import timedelta
        from ework_config.models import SiteConfig
        from ework_post.models import AbsPost
        
        self.stdout.write('🔍 Проверка истекших постов (тестовый режим):')
        self.stdout.write('-' * 50)
        
        config = SiteConfig.get_config()
        expiry_days = config.post_expiry_days
        expiry_date = timezone.now() - timedelta(days=expiry_days)
        
        expired_posts = AbsPost.objects.filter(
            status=3,
            is_deleted=False,
            created_at__lt=expiry_date
        ).select_related('user', 'sub_rubric')
        
        if not expired_posts:
            self.stdout.write(
                self.style.SUCCESS('✅ Нет истекших постов для архивирования')
            )
            return
        
        self.stdout.write(f'Найдено {expired_posts.count()} истекших постов:')
        self.stdout.write(f'Срок истечения: {expiry_days} дней')
        self.stdout.write(f'Дата отсечки: {expiry_date.strftime("%Y-%m-%d %H:%M:%S")}')
        self.stdout.write('-' * 30)
        
        for post in expired_posts[:10]:  # Показываем первые 10
            days_old = (timezone.now() - post.created_at).days
            self.stdout.write(
                f'ID: {post.id} | {post.title[:30]}... | '
                f'Возраст: {days_old} дней | Автор: {post.user.username}'
            )
        
        if expired_posts.count() > 10:
            remaining = expired_posts.count() - 10
            self.stdout.write(f'... и еще {remaining} постов')

    def archive_posts(self):
        """Архивировать истекшие посты"""
        self.stdout.write('🗂️  Архивирование истекших постов...')
        
        result = archive_expired_posts()
        
        if result['success']:
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Успешно архивировано {result["archived_count"]} постов'
                )
            )
            self.stdout.write(f'Срок хранения: {result["expiry_days"]} дней')
        else:
            self.stdout.write(
                self.style.ERROR(f'❌ Ошибка: {result["error"]}')
            )