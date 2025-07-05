"""
Фоновые задачи для автоматизации процессов eWork
"""
from django.utils import timezone
from datetime import timedelta
import logging

from ework_config.models import SiteConfig
from ework_post.models import AbsPost

logger = logging.getLogger(__name__)


def archive_expired_posts():
    """
    Архивирует истекшие посты на основе настроек SiteConfig.post_expiry_days
    Запускается ежедневно в 00:00
    """
    try:
        # Получаем конфигурацию сайта
        config = SiteConfig.get_config()
        expiry_days = config.post_expiry_days
        
        # Вычисляем дату истечения
        expiry_date = timezone.now() - timedelta(days=expiry_days)
        
        # Находим посты для архивирования
        expired_posts = AbsPost.objects.filter(
            status=3,  # Опубликованные
            is_deleted=False,
            created_at__lt=expiry_date
        )
        
        # Архивируем посты
        updated_count = expired_posts.update(status=4)  # Статус 4 = архив
        
        logger.info(f"Архивировано {updated_count} истекших постов (старше {expiry_days} дней)")
        
        return {
            'success': True,
            'archived_count': updated_count,
            'expiry_days': expiry_days,
            'expiry_date': expiry_date.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Ошибка при архивировании постов: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def cleanup_old_tasks():
    """
    Очистка старых выполненных задач Django-Q (опционально)
    """
    try:
        from django_q.models import Task
        
        # Удаляем задачи старше 7 дней
        cutoff_date = timezone.now() - timedelta(days=7)
        deleted_count, _ = Task.objects.filter(
            started__lt=cutoff_date,
            stopped__isnull=False  # Только завершенные задачи
        ).delete()
        
        logger.info(f"Удалено {deleted_count} старых задач Django-Q")
        
        return {
            'success': True,
            'deleted_count': deleted_count
        }
        
    except Exception as e:
        logger.error(f"Ошибка при очистке задач: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def get_expiry_stats():
    """
    Получить статистику по истекающим постам (для мониторинга)
    """
    try:
        config = SiteConfig.get_config()
        expiry_days = config.post_expiry_days
        
        now = timezone.now()
        expiry_date = now - timedelta(days=expiry_days)
        warning_date = now - timedelta(days=expiry_days - 3)  # За 3 дня до истечения
        
        # Статистика
        expired_count = AbsPost.objects.filter(
            status=3,
            is_deleted=False,
            created_at__lt=expiry_date
        ).count()
        
        expiring_soon_count = AbsPost.objects.filter(
            status=3,
            is_deleted=False,
            created_at__gte=expiry_date,
            created_at__lt=warning_date
        ).count()
        
        return {
            'expired_posts': expired_count,
            'expiring_soon': expiring_soon_count,
            'expiry_days': expiry_days,
            'next_cleanup': expiry_date.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Ошибка при получении статистики: {e}")
        return {
            'error': str(e)
        }