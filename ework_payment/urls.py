# urls.py
from django.urls import path
from .webhook_handlers import TelegramPaymentWebhookView

app_name = 'payment'

urlpatterns = [
    path('telegram-webhook/', TelegramPaymentWebhookView.as_view(), name='telegram_webhook'),
]
