import asyncio
import threading
from django.db.models.signals import post_save
from django.dispatch import receiver
from ework_services.models import PostServices
from .telegram_bot import send_telegram_message, send_telegram_message_with_keyboard
from ework_job.models import PostJob
from .utils import moderate_post
import logging

config = None
logger = logging.getLogger(__name__)


def moderate_post_async(instance):
    """Модерация поста в отдельном потоке"""
    try:
        if not config.auto_moderation_enabled and not config.manual_approval_required:
            # Нет модерации - сразу публикуем
            new_status = 3  # Опубликовано
            send_telegram_notification_async(instance)
        elif not config.auto_moderation_enabled and config.manual_approval_required:
            # Только ручная модерация
            new_status = 1  # На модерации
            send_admin_approval_notification(instance)
        elif config.auto_moderation_enabled and not config.manual_approval_required:
            # Только авто модерация
            goods_text = f"{instance.title}\n{instance.description}"
            is_approved = moderate_post(goods_text)
            if is_approved:
                new_status = 3  # Опубликовано
                send_telegram_notification_async(instance)
            else:
                new_status = 2  # Отклонено 
        else:
            # Авто + ручная модерация
            goods_text = f"{instance.title}\n{instance.description}"
            is_approved = moderate_post(goods_text)
            if is_approved:
                new_status = 1  # На модерации (ждем ручного одобрения)
                send_admin_approval_notification(instance)
            else:
                new_status = 2  # Отклонено
        type(instance).objects.filter(pk=instance.pk).update(status=new_status)
    except Exception as e:
        logger.error(f"❌ Ошибка при модерации поста: {e}")
        type(instance).objects.filter(pk=instance.pk).update(status=1)


#перенести в бот + .telegram_bot.py
# отправка поста админу для модерации
def send_admin_approval_notification(instance):
    """Отправка уведомления админам с кнопками одобрения/отклонения"""
    def send_notification():
        try:            
            if not config.bot_token or not config.admin_chat_id:
                return
            message = f"""
🔍 <b>Требуется модерация поста!</b>

📝 <b>Название:</b> {instance.title}
📄 <b>Описание:</b> {instance.description[:200]}{'...' if len(instance.description) > 200 else ''}
📂 <b>Категория:</b> {instance.sub_rubric.super_rubric.name}
📁 <b>Подкатегория:</b> {instance.sub_rubric.name}
💰 <b>Цена:</b> {instance.price} {instance.currency.code}
🏙️ <b>Город:</b> {instance.city.name}
👤 <b>Автор:</b> @{getattr(instance.user, 'username', 'неизвестен')}
            """.strip()
            
            # Создаем inline кнопки
            from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Одобрить", 
                        callback_data=f"approve_post_{instance.id}"
                    ),
                    InlineKeyboardButton(
                        text="❌ Отклонить", 
                        callback_data=f"reject_post_{instance.id}"
                    )
                ]
            ])
            asyncio.run(send_telegram_message_with_keyboard(
                config.bot_token, 
                config.admin_chat_id, 
                message,
                keyboard
            ))
        except Exception as e:
            logger.error(f"❌ Ошибка при отправке уведомления о модерации: {e}")

    thread = threading.Thread(target=send_notification)
    thread.daemon = True
    thread.start()

#перенести в бот + .telegram_bot.py
def send_telegram_notification_async(instance):
    """Отправка уведомления в Telegram в отдельном потоке"""
    def send_notification():
        try:            
            if not config.bot_token or not config.admin_chat_id:
                logger.error("❌ Нет токена или чата для отправки уведомления")
                return
            message = f"""
Объявление {instance.id}:
📝 <b>Название:</b> {instance.title}
📄 <b>Описание:</b> {instance.description[:200]}{'...' if len(instance.description) > 200 else ''}
📂 <b>Категория:</b> {instance.sub_rubric.super_rubric.name}
📁 <b>Подкатегория:</b> {instance.sub_rubric.name}
💰 <b>Цена:</b> {instance.price} {instance.currency.code}
🏙️ <b>Город:</b> {instance.city.name}
👤 <b>Автор:</b> @{getattr(instance.user, 'username', 'неизвестен')}
            """.strip()
            
            asyncio.run(send_telegram_message(
                config.bot_token, 
                config.admin_chat_id, 
                message, 
                parse_mode=None
            ))
            logger.error("Уведомление отправлено в Telegram")
        except Exception as e:
            logger.error(f"❌ Ошибка при отправке уведомления: {e}")

    
    thread = threading.Thread(target=send_notification)
    thread.daemon = True
    thread.start()


@receiver(post_save, sender=PostJob)
@receiver(post_save, sender=PostServices)
def handle_post_save(sender, instance, created, **kwargs):
    """
    Обработка создания/обновления поста
    ВАЖНО: Модерация запускается только для статуса 0 (На модерации)
    """    
    if instance.status == 0:
        type(instance).objects.filter(pk=instance.pk).update(status=1)
        thread = threading.Thread(target=moderate_post_async, args=(instance,))
        thread.daemon = True
        thread.start()
    else:
        logger.warning(f"⏸️ Модерация пропущена для поста {instance.title} (статус: {instance.get_status_display()})")


@receiver(post_save, sender='ework_premium.Payment')
def handle_payment_save(sender, instance, created, **kwargs):
    """
    Обработка изменения статуса платежа
    Когда платеж становится оплаченным - отправляем пост на модерацию
    """    
    if instance.status == 'paid' and instance.post:
        # Применяем аддоны к посту
        instance.post.apply_addons_from_payment(instance)
        # Переводим пост из черновика на модерацию
        old_status = instance.post.status
        instance.post.status = 0  # Это должно вызвать handle_post_save
        instance.post.save(update_fields=['status'])
        # Проверяем что статус действительно изменился
        instance.post.refresh_from_db()
        # Если статус не изменился, принудительно вызываем модерацию
        if instance.post.status == 0:
            from threading import Thread
            thread = Thread(target=moderate_post_async, args=(instance.post,))
            thread.daemon = True
            thread.start()
    else:
        logger.warning(f"⏸️ Модерация пропущена для платежа {instance.id} (статус: {instance.status})")

