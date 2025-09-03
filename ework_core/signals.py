
import threading
from django.db.models.signals import post_save
from django.dispatch import receiver
from ework_bot_tg.bot import bot
from ework_services.models import PostServices
from ework_job.models import PostJob
from asgiref.sync import async_to_sync, sync_to_async
from .utils import moderate_post
from ework_config.utils import get_config
import logging

logger = logging.getLogger(__name__)

async def moderate_post_async(instance):
    """Модерация поста асинхронно"""
    try:
        config = get_config()
        if not config.auto_moderation_enabled and not config.manual_approval_required:
            # Нет модерации - сразу публикуем
            logger.warning("⏸️⏸️⏸️⏸️⏸️ Нет модерации - сразу публикуем")
            new_status = 3  # Опубликовано
            await bot.send_telegram_city_chat(instance)

        elif not config.auto_moderation_enabled and config.manual_approval_required:
            # Только ручная модерация
            logger.warning("⏸️⏸️⏸️⏸️⏸️ Только ручная модерация")
            new_status = 1  # На модерации
            await bot.send_admin_approval_notification(instance)

        elif config.auto_moderation_enabled and not config.manual_approval_required:
            # Только авто модерация
            goods_text = f"{instance.title}\n{instance.description}"
            is_approved = moderate_post(goods_text)
            if is_approved:
                new_status = 3  # Опубликовано
                await bot.send_telegram_city_chat(instance)
            else:
                new_status = 2  # Отклонено
                text = "Только авто модерация - Отклонено."
                await bot.send_telegram_error_mes(text)
        else:
            # Авто + ручная модерация
            goods_text = f"{instance.title}\n{instance.description}"
            is_approved = moderate_post(goods_text)
            if is_approved:
                new_status = 1  # На модерации (ждем ручного одобрения)
                # send_admin_approval_notification(instance)
                await bot.send_telegram_error_mes(text = "На модерации (ждем ручного одобрения)")
            else:
                new_status = 2  # Отклонено

        await sync_to_async(type(instance).objects.filter(pk=instance.pk).update)(status=new_status)

    except Exception as e:
        text=str(e)
        await bot.send_telegram_error_mes(text)
        logger.error(f"❌ Ошибка при модерации поста: {e}")
        type(instance).objects.filter(pk=instance.pk).update(status=1)



@receiver(post_save, sender=PostJob)
@receiver(post_save, sender=PostServices)
def handle_post_save(sender, instance, created, **kwargs):
    """
    Обработка создания/обновления поста
    ВАЖНО: Модерация запускается только для статуса 0 (На модерации)
    """    
    if created:
        logger.warning("⏸️ Модерация для поста")
        async_to_sync(moderate_post_async)(instance)
    else:
        logger.warning(f"⏸️ Модерация пропущена для поста {instance.title} (статус: {instance.get_status_display()})")


# @receiver(post_save, sender='ework_premium.Payment')
# def handle_payment_save(sender, instance, created, **kwargs):
#     """
#     Обработка изменения статуса платежа
#     Когда платеж становится оплаченным - отправляем пост на модерацию
#     """    
#     if instance.status == 'paid' and instance.post:
#         instance.post.apply_addons_from_payment(instance)
#         old_status = instance.post.status
#         instance.post.status = 0 
#         instance.post.save(update_fields=['status'])
#         instance.post.refresh_from_db()  # Обновляем инстанс поста из БД
        
#         if instance.post.status == 0:
#             # Запускаем модерацию в отдельном потоке
#             import threading
#             thread = threading.Thread(target=moderate_post_async, args=(instance.post,))
#             thread.daemon = True
#             thread.start()
#     else:
#         logger.warning(f"⏸️ Модерация пропущена для платежа {instance.id} (статус: {instance.status})")


