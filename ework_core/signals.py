import threading
from django.db.models.signals import post_save
from django.dispatch import receiver
from ework_bot_tg.bot.bot import (
    send_telegram_city_chat,
    send_admin_approval_notification,
    send_telegram_error_mes,
    bot,
)
from ework_services.models import PostServices
from ework_job.models import PostJob
from .utils import moderate_post
from ework_config.utils import get_config
from typing import TypedDict

import asyncio
from logger_config import logger
from asgiref.sync import sync_to_async


class PostState(TypedDict):
    post_id: int
    title: str
    description: str
    price: int
    sub_rubric: str
    city: str
    city_chat_id: int
    address: str | None
    username: str
    phone_user: int | None


def run_async_in_thread(func, *args, **kwargs):
    """Запускает асинхронную функцию в отдельном потоке с собственным циклом событий."""
    def wrapper():
        asyncio.run(func(*args, **kwargs))

    thread = threading.Thread(target=wrapper)
    thread.daemon = True
    thread.start()


def update_post_status(instance, status: int):
    """Синхронное обновление статуса поста."""
    type(instance).objects.filter(pk=instance.pk).update(status=status)


async def moderate_post_async(instance):
    """Модерация поста асинхронно"""

    data: PostState = {
        "post_id": instance.id,
        "title": instance.title,
        "description": instance.description,
        "price": instance.price,
        "sub_rubric": instance.sub_rubric,
        "city": instance.city,
        "city_chat_id": instance.city.chat_id,
        "address": instance.address,
        "username": instance.user.username,
        "phone_user": instance.user_phone,
    }

    try:
        config = get_config()
        if not config.auto_moderation_enabled and not config.manual_approval_required:
            new_status = 3  # Опубликовано
            await send_telegram_city_chat(data)

        elif not config.auto_moderation_enabled and config.manual_approval_required:
            new_status = 1  # На модерации
            try:
                await send_admin_approval_notification(data)
            except Exception as e:
                logger.error(f"Ошибка отправки поста только с ручной модерацией - {e}")

        elif config.auto_moderation_enabled and not config.manual_approval_required:
            # Только авто модерация
            goods_text = f"{data['title']}\n{data['description']}"
            is_approved = moderate_post(goods_text)
            if is_approved:
                new_status = 3  # Опубликовано
                try:
                    await send_telegram_city_chat(data)
                except Exception as e:
                    logger.error(f"Ошибка отправки поста только с авто модерацией - {e}")
            else:
                new_status = 2  # Отклонено
                logger.warning("❌ Только авто модерация - Отклонено.")
        else:
            # Авто + ручная модерация
            goods_text = f"{data['title']}\n{data['description']}"
            is_approved = moderate_post(goods_text)
            if is_approved:
                new_status = 1  # На модерации (ждем ручного одобрения)
                try:
                    await send_admin_approval_notification(data)
                except Exception as e:
                    logger.error(f"Ошибка отправки поста Авто + ручная модерация - {e}")
            else:
                new_status = 2  # Отклонено

        try:
            await sync_to_async(update_post_status)(instance, new_status)
        except Exception as e:
            logger.error(f"Ошибка изменения статуса поста - {e}")

    except Exception as e:
        logger.error(f"❌ Ошибка при модерации поста: {e}")
        await sync_to_async(update_post_status)(instance, 1)
    finally:
        await bot.session.close()


@receiver(post_save, sender=PostJob)
@receiver(post_save, sender=PostServices)
def handle_post_save(sender, instance, created, **kwargs):
    """
    Обработка создания/обновления поста
    ВАЖНО: Модерация запускается только для статуса 0 (На модерации)
    """
    if created:
        logger.warning("⏸️ Модерация для поста")
        run_async_in_thread(moderate_post_async, instance)
    else:
        logger.warning(
            f"⏸️ Модерация пропущена для поста {instance.title} (статус: {instance.get_status_display()})"
        )



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


