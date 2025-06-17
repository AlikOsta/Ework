import asyncio
import threading
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from ework_services.models import PostServices
from .telegram_bot import send_telegram_message
from ework_job.models import PostJob
from .utils import moderate_post

YOUR_PERSONAL_CHAT_ID = 7727039536
TELEGRAM_BOT_TOKEN = "7662590757:AAHpuX8hKUO8aCk3nGWsedA286qh0G0OAzw"

def moderate_post_async(instance):
    """Модерация поста в отдельном потоке"""
    try:
        print(f"Начало модерации поста: {instance.title}")
        
        goods_text = f"{instance.title}\n{instance.description}"
        is_approved = moderate_post(goods_text)
        
        if is_approved:
            new_status = 3  # Одобрено
            print("Пост одобрен модерацией")

            send_telegram_notification_async(instance)
        else:
            new_status = 2  # Отклонено
            print("Пост отклонен модерацией")
        
        type(instance).objects.filter(pk=instance.pk).update(status=new_status)
        
    except Exception as e:
        print(f"Ошибка при модерации: {e}")
        type(instance).objects.filter(pk=instance.pk).update(status=1)

def send_telegram_notification_async(instance):
    """Отправка уведомления в Telegram в отдельном потоке"""
    def send_notification():
        try:
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
                TELEGRAM_BOT_TOKEN, 
                YOUR_PERSONAL_CHAT_ID, 
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
