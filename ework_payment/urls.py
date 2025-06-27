# urls.py
from django.urls import path
from .views import create_payment
from .webhook_handlers import TelegramPaymentWebhookView

app_name = 'payment'

urlpatterns = [
    path('create_payment/', create_payment, name='create_payment'),
    path('telegram-webhook/', TelegramPaymentWebhookView.as_view(), name='telegram_webhook'),
]
