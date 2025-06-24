"""
Management команда для обработки модерации постов
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from ework_post.models import AbsPost
from ework_payment.services import PostPublicationService
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Обработка модерации постов'

    def add_arguments(self, parser):
        parser.add_argument(
            '--post-id',
            type=int,
            help='ID конкретного поста для обработки'
        )
        parser.add_argument(
            '--action',
            choices=['approve', 'reject'],
            help='Действие: approve (одобрить) или reject (отклонить)'
        )
        parser.add_argument(
            '--auto-approve',
            action='store_true',
            help='Автоматически одобрить все посты на модерации (для тестирования)'
        )

    def handle(self, *args, **options):
        post_id = options.get('post_id')
        action = options.get('action')
        auto_approve = options.get('auto_approve')

        if auto_approve:
            self.auto_approve_posts()
        elif post_id and action:
            self.process_single_post(post_id, action)
        else:
            self.show_pending_posts()

    def auto_approve_posts(self):
        """Автоматически одобрить все посты на модерации"""
        pending_posts = AbsPost.objects.filter(status=0, is_deleted=False)
        count = 0
        
        for post in pending_posts:
            try:
                post.status = 3  # Опубликовано
                post.save()
                count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Одобрен пост #{post.id}: {post.title}')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Ошибка при одобрении поста #{post.id}: {e}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Всего одобрено постов: {count}')
        )

    def process_single_post(self, post_id, action):
        """Обработать один пост"""
        try:
            post = AbsPost.objects.get(id=post_id, is_deleted=False)
            
            if action == 'approve':
                post.status = 3  # Опубликовано
                post.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Пост #{post_id} одобрен и опубликован')
                )
            elif action == 'reject':
                post.status = 2  # Заблокировано
                post.save()
                
                # Обрабатываем отклонение (возврат денег и т.д.)
                PostPublicationService.handle_moderation_rejection(post)
                
                self.stdout.write(
                    self.style.WARNING(f'Пост #{post_id} отклонен')
                )
                
        except AbsPost.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Пост с ID {post_id} не найден')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Ошибка при обработке поста #{post_id}: {e}')
            )

    def show_pending_posts(self):
        """Показать все посты на модерации"""
        pending_posts = AbsPost.objects.filter(status=0, is_deleted=False).select_related('user', 'package')
        
        if not pending_posts.exists():
            self.stdout.write(
                self.style.SUCCESS('Нет постов на модерации')
            )
            return
        
        self.stdout.write(
            self.style.WARNING(f'Постов на модерации: {pending_posts.count()}')
        )
        self.stdout.write('')
        
        for post in pending_posts:
            package_info = f" (Тариф: {post.package.name})" if post.package else ""
            self.stdout.write(f'#{post.id} - {post.title[:50]}...{package_info}')
            self.stdout.write(f'   Автор: {post.user.username}')
            self.stdout.write(f'   Создан: {post.created_at}')
            self.stdout.write('')
        
        self.stdout.write('Используйте:')
        self.stdout.write('  --post-id X --action approve  - одобрить пост')
        self.stdout.write('  --post-id X --action reject   - отклонить пост')
        self.stdout.write('  --auto-approve                - одобрить все посты')