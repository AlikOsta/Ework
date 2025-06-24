from django.urls import path
from . import views
from .simple_webhook import simple_payment_webhook, test_payment_webhook

app_name = 'payments'

urlpatterns = [
    # API для создания платежа
    path('api/create/', views.create_payment, name='create_payment'),
    
    # Простой webhook для уведомлений от Telegram бота
    path('webhook/simple/', simple_payment_webhook, name='simple_webhook'),
    
    # Тестовый webhook
    path('webhook/test/', test_payment_webhook, name='test_webhook'),
    
    # Callback от Telegram (оригинальный)
    path('api/telegram/callback/', views.telegram_payment_callback, name='telegram_callback'),
    
    # Проверка статуса платежа
    path('api/status/<int:payment_id>/', views.payment_status, name='payment_status'),
    
    # Страницы результата платежа
    path('success/<int:payment_id>/', views.payment_success, name='payment_success'),
    path('cancel/<int:payment_id>/', views.payment_cancel, name='payment_cancel'),
]