import asyncio
import threading
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from ework_services.models import PostServices
from .telegram_bot import send_telegram_message, send_telegram_message_with_keyboard
from ework_job.models import PostJob
from .utils import moderate_post

# YOUR_PERSONAL_CHAT_ID and TELEGRAM_BOT_TOKEN moved to SiteConfig

def moderate_post_async(instance):
    """Модерация поста в отдельном потоке"""
    try:
        print(f"Начало модерации поста: {instance.title}")
        
        # Получаем настройки модерации
        from ework_config.utils import get_config
        config = get_config()
        
        # Логика модерации
        if not config.auto_moderation_enabled and not config.manual_approval_required:
            # Нет модерации - сразу публикуем
            new_status = 3  # Опубликовано
            print("Пост опубликован без модерации")
            send_telegram_notification_async(instance)
        elif not config.auto_moderation_enabled and config.manual_approval_required:
            # Только ручная модерация
            new_status = 1  # На модерации
            print("Пост направлен на ручную модерацию")
            send_admin_approval_notification(instance)
        elif config.auto_moderation_enabled and not config.manual_approval_required:
            # Только авто модерация
            goods_text = f"{instance.title}\n{instance.description}"
            is_approved = moderate_post(goods_text)
            if is_approved:
                new_status = 3  # Опубликовано
                print("Пост одобрен ИИ модерацией и опубликован")
                send_telegram_notification_async(instance)
            else:
                new_status = 2  # Отклонено
                print("Пост отклонен ИИ модерацией")
                refund_if_paid(instance)
        else:
            # Авто + ручная модерация
            goods_text = f"{instance.title}\n{instance.description}"
            is_approved = moderate_post(goods_text)
            if is_approved:
                new_status = 1  # На модерации (ждем ручного одобрения)
                print("Пост прошел ИИ модерацию, отправляем на ручную проверку")
                send_admin_approval_notification(instance)
            else:
                new_status = 2  # Отклонено
                print("Пост отклонен ИИ модерацией")
                refund_if_paid(instance)
        
        type(instance).objects.filter(pk=instance.pk).update(status=new_status)
        
    except Exception as e:
        print(f"Ошибка при модерации: {e}")
        type(instance).objects.filter(pk=instance.pk).update(status=1)


def refund_if_paid(instance):
    """Возврат денег если пост был платным"""
    try:
        from ework_premium.models import Payment
        # Ищем платеж за этот пост
        payment = Payment.objects.filter(post=instance, status='paid').first()
        if payment:
            payment.status = 'refunded'
            payment.save()
            print(f"💰 Возвращены деньги за отклоненный пост: {payment.amount} руб.")
            # Здесь можно добавить реальный возврат через платежную систему
    except Exception as e:
        print(f"❌ Ошибка возврата денег: {e}")


def send_admin_approval_notification(instance):
    """Отправка уведомления админам с кнопками одобрения/отклонения"""
    def send_notification():
        try:
            # Получаем конфигурацию
            from ework_config.utils import get_config
            config = get_config()
            
            if not config.notification_bot_token or not config.admin_chat_id:
                print("Telegram уведомления отключены - нет токена или chat_id")
                return
            
            message = f"""
🔍 <b>Требуется модерация поста!</b>

📝 <b>Название:</b> {instance.title}
📄 <b>Описание:</b> {instance.description[:200]}{'...' if len(instance.description) > 200 else ''}
📂 <b>Категория:</b> {instance.sub_rubric.super_rubric.name}
📁 <b>Подкатегория:</b> {instance.sub_rubric.name}
💰 <b>Цена:</b> {instance.price} {instance.currency.code}
🏙️ <b>Город:</b> {instance.city.name}
👤 <b>Автор:</b> @{instance.user.username}

#moderation #post_id_{instance.id}
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
                ],
                [
                    InlineKeyboardButton(
                        text="📝 Посмотреть в админке", 
                        url=f"{config.site_url}/admin/ework_job/postjob/{instance.id}/change/" if hasattr(instance, 'experience') else f"{config.site_url}/admin/ework_services/postservices/{instance.id}/change/"
                    )
                ]
            ])
            
            asyncio.run(send_telegram_message_with_keyboard(
                config.notification_bot_token, 
                config.admin_chat_id, 
                message,
                keyboard
            ))
            print("Уведомление о модерации отправлено в Telegram")
        except Exception as e:
            print(f"Ошибка при отправке уведомления о модерации: {e}")
    
    thread = threading.Thread(target=send_notification)
    thread.daemon = True
    thread.start()


def send_telegram_notification_async(instance):
    """Отправка уведомления в Telegram в отдельном потоке"""
    def send_notification():
        try:
            # Получаем конфигурацию
            from ework_config.utils import get_config
            config = get_config()
            
            if not config.notification_bot_token or not config.admin_chat_id:
                print("Telegram уведомления отключены - нет токена или chat_id")
                return
            
            message = f"""
Новое объявление:
Название: {instance.title}
Описание: {instance.description}
Категория: {instance.sub_rubric.super_rubric.name}
Подкатегория: {instance.sub_rubric.name}
Цена: {instance.price} {instance.currency.code}
Город: {instance.city.name}
Автор: @{instance.user.username}
            """.strip()
            
            asyncio.run(send_telegram_message(
                config.notification_bot_token, 
                config.admin_chat_id, 
                message, 
                parse_mode=None
            ))
            print("Уведомление отправлено в Telegram")
        except Exception as e:
            print(f"Ошибка при отправке в Telegram: {e}")
    
    thread = threading.Thread(target=send_notification)
    thread.daemon = True
    thread.start()

@receiver(post_save, sender=PostJob)
@receiver(post_save, sender=PostServices)
def handle_post_save(sender, instance, created, **kwargs):
    if created or instance.status == 0:
        print(f"Получен сигнал post_save от {sender.__name__}")
        
        type(instance).objects.filter(pk=instance.pk).update(status=1)
        
        thread = threading.Thread(target=moderate_post_async, args=(instance,))
        thread.daemon = True
        thread.start()
        print("Модерация запущена в фоновом режиме")
