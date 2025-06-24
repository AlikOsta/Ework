from django.urls import path
from . import views
from .telegram_webhook import telegram_payment_webhook

app_name = 'payments'

urlpatterns = [
    # API для создания платежа
    path('api/create/', views.create_payment, name='create_payment'),
    
    # Callback от Telegram
    path('api/telegram/callback/', views.telegram_payment_callback, name='telegram_callback'),
    
    # Webhook от Telegram Bot API для платежей
    path('webhook/telegram/', telegram_payment_webhook, name='telegram_webhook'),
    
    # Проверка статуса платежа
    path('api/status/<int:payment_id>/', views.payment_status, name='payment_status'),
    
    # Страницы результата платежа
    path('success/<int:payment_id>/', views.payment_success, name='payment_success'),
    path('cancel/<int:payment_id>/', views.payment_cancel, name='payment_cancel'),
]