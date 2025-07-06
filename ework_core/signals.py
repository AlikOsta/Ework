import asyncio
import threading
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from ework_services.models import PostServices
from .telegram_bot import send_telegram_message, send_telegram_message_with_keyboard
from ework_job.models import PostJob
from .utils import moderate_post


def moderate_post_async(instance):
    """Модерация поста в отдельном потоке"""
    try:
        print(f"🔄 Начало модерации поста: {instance.title}")
        
        # Получаем настройки модерации
        from ework_config.utils import get_config
        config = get_config()
        
        print(f"⚙️ Настройки модерации:")
        print(f"   auto_moderation_enabled: {config.auto_moderation_enabled}")
        print(f"   manual_approval_required: {config.manual_approval_required}")
        
        # Логика модерации
        if not config.auto_moderation_enabled and not config.manual_approval_required:
            # Нет модерации - сразу публикуем
            new_status = 3  # Опубликовано
            print("📢 Пост опубликован без модерации")
            send_telegram_notification_async(instance)
        elif not config.auto_moderation_enabled and config.manual_approval_required:
            # Только ручная модерация
            new_status = 1  # На модерации
            print("👤 Пост направлен на ручную модерацию")
            send_admin_approval_notification(instance)
        elif config.auto_moderation_enabled and not config.manual_approval_required:
            # Только авто модерация
            goods_text = f"{instance.title}\n{instance.description}"
            is_approved = moderate_post(goods_text)
            if is_approved:
                new_status = 3  # Опубликовано
                print("🤖 Пост одобрен ИИ модерацией и опубликован")
                send_telegram_notification_async(instance)
            else:
                new_status = 2  # Отклонено
                print("❌ Пост отклонен ИИ модерацией")
                refund_if_paid(instance)
        else:
            # Авто + ручная модерация
            goods_text = f"{instance.title}\n{instance.description}"
            is_approved = moderate_post(goods_text)
            if is_approved:
                new_status = 1  # На модерации (ждем ручного одобрения)
                print("🤖➡️👤 Пост прошел ИИ модерацию, отправляем на ручную проверку")
                send_admin_approval_notification(instance)
            else:
                new_status = 2  # Отклонено
                print("❌ Пост отклонен ИИ модерацией")
                refund_if_paid(instance)
        
        print(f"📊 Устанавливаем новый статус: {new_status}")
        type(instance).objects.filter(pk=instance.pk).update(status=new_status)
        
    except Exception as e:
        print(f"❌ Ошибка при модерации: {e}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
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
👤 <b>Автор:</b> @{getattr(instance.user, 'username', 'неизвестен')}

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
                        url=f"{config.site_url}/admin/ework_post/postjob/{instance.id}/change/" if hasattr(instance, 'experience') else f"{config.site_url}/admin/ework_post/postservices/{instance.id}/change/"
                    )
                ]
            ])
            
            print(f"📤 Отправляем уведомление о модерации поста {instance.id}")
            
            asyncio.run(send_telegram_message_with_keyboard(
                config.notification_bot_token, 
                config.admin_chat_id, 
                message,
                keyboard
            ))
            print("✅ Уведомление о модерации отправлено в Telegram")
        except Exception as e:
            print(f"❌ Ошибка при отправке уведомления о модерации: {e}")
            import traceback
            print(f"❌ Traceback: {traceback.format_exc()}")
    
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
    """
    Обработка создания/обновления поста
    ВАЖНО: Модерация запускается только для статуса 0 (На модерации)
    """
    print(f"🔔 Сигнал handle_post_save: post_id={instance.id}, status={instance.status} ({instance.get_status_display()}), created={created}")
    
    # Запускаем модерацию только если статус = 0 (На модерации)
    if instance.status == 0:
        print(f"🔄 Запуск модерации для поста {instance.title} (статус: {instance.get_status_display()})")
        
        # Переводим в статус "На модерации" чтобы избежать повторных срабатываний
        type(instance).objects.filter(pk=instance.pk).update(status=1)
        
        # Запускаем модерацию в фоне
        thread = threading.Thread(target=moderate_post_async, args=(instance,))
        thread.daemon = True
        thread.start()
        print("✅ Модерация запущена в фоновом режиме")
    else:
        print(f"⏸️ Модерация пропущена для поста {instance.title} (статус: {instance.get_status_display()})")



@receiver(post_save, sender='ework_premium.Payment')
def handle_payment_save(sender, instance, created, **kwargs):
    """
    Обработка изменения статуса платежа
    Когда платеж становится оплаченным - отправляем пост на модерацию
    """
    print(f"🔔 Сигнал handle_payment_save: payment_id={instance.id}, status={instance.status}, created={created}")
    
    if instance.status == 'paid' and instance.post:
        print(f"💰 Платеж оплачен! Отправляем пост {instance.post.title} на модерацию")
        print(f"📊 Текущий статус поста ДО изменения: {instance.post.status} ({instance.post.get_status_display()})")
        
        # Проверяем, это переопубликация или обычный пост
        copy_from_id = None
        if instance.addons_data and 'copy_from_id' in instance.addons_data:
            copy_from_id = instance.addons_data['copy_from_id']
            print(f"🔄 DEBUG: Это переопубликация поста {copy_from_id}")
        else:
            print(f"🔄 DEBUG: Это обычный пост, не переопубликация")
        
        # Применяем аддоны к посту
        instance.post.apply_addons_from_payment(instance)
        
        # Если это переопубликация, обрабатываем старый пост
        if copy_from_id:
            _handle_republish_after_payment(copy_from_id, instance.post, instance.user)
        
        # Переводим пост из черновика на модерацию
        old_status = instance.post.status
        instance.post.status = 0  # Это должно вызвать handle_post_save
        instance.post.save(update_fields=['status'])
        
        # Проверяем что статус действительно изменился
        instance.post.refresh_from_db()
        print(f"✅ Статус поста изменен с {old_status} на {instance.post.status} ({instance.post.get_status_display()})")
        
        # Если статус не изменился, принудительно вызываем модерацию
        if instance.post.status == 0:
            print("🔄 Принудительно запускаем модерацию...")
            from threading import Thread
            thread = Thread(target=moderate_post_async, args=(instance.post,))
            thread.daemon = True
            thread.start()
        
    else:
        print(f"⏸️ Условие не выполнено: status={instance.status}, post={instance.post}")


def _handle_republish_after_payment(old_post_id, new_post, user):
    """Обработка переопубликации после оплаты"""
    print(f"🔄 DEBUG: _handle_republish_after_payment вызван с old_post_id={old_post_id}, new_post_id={new_post.id}, user={user.username}")
    try:
        from ework_post.models import AbsPost
        from ework_post.views import copy_post_views
        
        old_post = AbsPost.objects.get(
            id=old_post_id,
            user=user,
            status=4,  # Архивный
            is_deleted=False
        )
        
        print(f"🔄 DEBUG: Найден старый пост {old_post_id}, статус ДО: {old_post.status}")
        
        # Копируем статистику просмотров
        copied_views = copy_post_views(old_post, new_post)
        
        # Помечаем старый пост как удаленный
        old_post.soft_delete()
        
        print(f"🔄 DEBUG: Переопубликация после оплаты завершена: скопировано {copied_views} просмотров, старый пост {old_post_id} помечен как удаленный, новый статус: {old_post.status}")
        
    except AbsPost.DoesNotExist:
        print(f"❌ DEBUG: Старый пост {old_post_id} не найден при переопубликации после оплаты")
    except Exception as e:
        print(f"❌ DEBUG: Ошибка при обработке переопубликации после оплаты: {e}")
        import traceback
        print(f"❌ DEBUG: Traceback: {traceback.format_exc()}")
