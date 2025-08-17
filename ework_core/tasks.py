import logging
from datetime import timedelta
from django.utils import timezone
from django.db.models import Q

from ework_post.models import AbsPost
from ework_config.models import SiteConfig

logger = logging.getLogger(__name__)

def archive_expired_posts():
    """
    Архивация объявлений с истекшим сроком жизни
    Выполняется раз в 24 часа
    """
    try:
        config = SiteConfig.get_config()
        expiry_days = config.post_expiry_days
        expiry_date = timezone.now() - timedelta(days=expiry_days)
        
        expired_posts = AbsPost.objects.filter(
            Q(status=3) &  # Только опубликованные
            Q(created_at__lt=expiry_date) &  # Созданные раньше срока истечения
            Q(is_deleted=False)  # Не удаленные
        )
        
        expired_count = expired_posts.count()
        logger.info(f"Найдено {expired_count} истекших постов для архивации")
        
        if expired_count > 0:
            updated_count = expired_posts.update(status=4)
            logger.info(f"Успешно архивировано {updated_count} постов")

        else:
            logger.info("Нет истекших постов для архивации")
            
        return {
            'success': True,
            'archived_count': expired_count,
            'message': f'Архивировано {expired_count} постов'
        }
        
    except Exception as e:
        logger.error(f"Ошибка при архивации истекших постов: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'message': 'Ошибка при архивации постов'
        }