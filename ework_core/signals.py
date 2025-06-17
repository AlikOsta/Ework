from django.db.models.signals import post_save
from django.dispatch import receiver

from ework_job.models import PostJob
from ework_services.models import PostServices

from .telegram_bot import send_telegram_message
import asyncio

YOUR_PERSONAL_CHAT_ID = 7727039536
TELEGRAM_BOT_TOKEN = "7662590757:AAHpuX8hKUO8aCk3nGWsedA286qh0G0OAzw"


@receiver(post_save, sender=PostJob)
@receiver(post_save, sender=PostServices)
def handle_post_save(sender, instance, created, **kwargs):
    if created:
        message = f"""
Новое объявление:
Название: {instance.title}
Описание: {instance.description}
Категория: {instance.sub_rubric.super_rubric.name}
Подкатегория: {instance.sub_rubric.name}
Цена: {instance.price} {instance.currency.code}
Город: {instance.city.name}
Автор: @{instance.user.username}
Ссылка: {instance.get_absolute_url()}
        """.strip()
        
        try:
            asyncio.run(send_telegram_message(TELEGRAM_BOT_TOKEN, YOUR_PERSONAL_CHAT_ID, message, parse_mode='HTML'))
        except Exception as e:
            print(f"Ошибка при отправке в Telegram: {e}")