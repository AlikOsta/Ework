from django.db.models.signals import post_save
from django.dispatch import receiver

from ework_post.models import AbsPost
from ework_job.models import PostJob
from ework_services.models import PostServices

from .telegram_bot import send_telegram_message
import asyncio
from .utils import moderate_post

YOUR_PERSONAL_CHAT_ID = 7727039536
TELEGRAM_BOT_TOKEN = "7662590757:AAHpuX8hKUO8aCk3nGWsedA286qh0G0OAzw"


@receiver(post_save, sender=PostJob)
@receiver(post_save, sender=PostServices)
def handle_post_save(sender, instance, created, **kwargs):
    print(f"Получен сигнал post_save от {sender.__name__}")

    if created or instance.status == 0:
        goods_text = f"{instance.title}\n{instance.description}"
        
        if moderate_post(goods_text):
            instance.status = 3

            massage = f"Новое объявление: {instance.title}\n\nОписание: {instance.description}"

            asyncio.run(send_telegram_message(TELEGRAM_BOT_TOKEN, YOUR_PERSONAL_CHAT_ID, massage))
        else:
            instance.status = 2 
            
        type(instance).objects.filter(pk=instance.pk).update(status=instance.status)