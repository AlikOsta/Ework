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
        # Получаем конфигурацию
        config = SiteConfig.get_config()
        expiry_days = config.post_expiry_days
        
        # Вычисляем дату, после которой посты считаются истекшими
        expiry_date = timezone.now() - timedelta(days=expiry_days)
        
        # Находим все опубликованные посты, которые старше указанного срока
        expired_posts = AbsPost.objects.filter(
            Q(status=3) &  # Только опубликованные
            Q(created_at__lt=expiry_date) &  # Созданные раньше срока истечения
            Q(is_deleted=False)  # Не удаленные
        )
        
        # Логируем количество найденных постов
        expired_count = expired_posts.count()
        logger.info(f"Найдено {expired_count} истекших постов для архивации")
        
        if expired_count > 0:
            # Обновляем статус на "архив" (статус 4)
            updated_count = expired_posts.update(status=4)
            logger.info(f"Успешно архивировано {updated_count} постов")
            
            # Логируем детали архивированных постов
            for post in expired_posts[:10]:  # Логируем первые 10 для примера
                logger.info(f"Архивирован пост: ID={post.id}, Название='{post.title}', "
                           f"Создан={post.created_at.strftime('%Y-%m-%d %H:%M')}")
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