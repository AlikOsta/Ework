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


def remove_expired_highlights():
    """
    Убирает выделение цветом у постов с истекшим сроком
    Запускается ежедневно
    """
    try:
        now = timezone.now()
        
        # Находим посты с истекшим выделением
        expired_highlights = AbsPost.objects.filter(
            has_highlight_addon=True,
            highlight_expires_at__lt=now,
            is_premium=True
        )
        
        # Убираем выделение
        updated_count = 0
        for post in expired_highlights:
            post.is_premium = False
            post.has_highlight_addon = False
            post.highlight_expires_at = None
            post.save(update_fields=['is_premium', 'has_highlight_addon', 'highlight_expires_at'])
            updated_count += 1
        
        logger.info(f"Убрано выделение у {updated_count} постов с истекшим сроком")
        
        return {
            'success': True,
            'removed_highlights': updated_count
        }
        
    except Exception as e:
        logger.error(f"Ошибка при удалении истекших выделений: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def remove_expired_photo_addons():
    """
    Убирает услугу фото у постов с истекшим сроком
    Запускается ежедневно
    """
    try:
        now = timezone.now()
        
        # Находим посты с истекшей услугой фото
        expired_photos = AbsPost.objects.filter(
            has_photo_addon=True,
            photo_expires_at__lt=now
        )
        
        # Убираем услугу фото
        updated_count = 0
        for post in expired_photos:
            post.has_photo_addon = False
            post.photo_expires_at = None
            post.save(update_fields=['has_photo_addon', 'photo_expires_at'])
            updated_count += 1
        
        logger.info(f"Убрана услуга фото у {updated_count} постов с истекшим сроком")
        
        return {
            'success': True,
            'removed_photo_addons': updated_count
        }
        
    except Exception as e:
        logger.error(f"Ошибка при удалении истекших фото услуг: {e}")
        return {
            'success': False,
            'error': str(e)
        }