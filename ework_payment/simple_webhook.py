"""
Простой webhook для обработки платежей от Telegram бота
"""
import json
import logging
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from ework_premium.models import Payment
from ework_payment.services import PaymentService, PostPublicationService
from ework_post.models import AbsPost

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def simple_payment_webhook(request):
    """
    Простой webhook для обработки уведомлений об оплате от Telegram бота
    
    Ожидаемый формат данных:
    {
        "payment_id": 123,
        "status": "paid" | "failed",
        "telegram_payment_charge_id": "xxx",
        "provider_payment_charge_id": "yyy"
    }
    """
    try:
        data = json.loads(request.body.decode('utf-8'))
        
        payment_id = data.get('payment_id')
        status = data.get('status')
        telegram_charge_id = data.get('telegram_payment_charge_id')
        provider_charge_id = data.get('provider_payment_charge_id')
        
        if not payment_id or not status:
            return JsonResponse({'error': 'Missing payment_id or status'}, status=400)
        
        try:
            payment = Payment.objects.get(id=payment_id)
        except Payment.DoesNotExist:
            return JsonResponse({'error': 'Payment not found'}, status=404)
        
        if status == 'paid':
            # Обрабатываем успешный платеж
            if PaymentService.process_successful_payment(payment, telegram_charge_id, provider_charge_id):
                # Находим и публикуем пост
                publish_post_after_payment(payment)
                
                logger.info(f"Платеж {payment.order_id} успешно обработан")
                return JsonResponse({'success': True, 'message': 'Payment processed successfully'})
            else:
                logger.error(f"Не удалось обработать платеж {payment.order_id}")
                return JsonResponse({'error': 'Failed to process payment'}, status=500)
                
        elif status == 'failed':
            # Обрабатываем неудачный платеж
            PaymentService.process_failed_payment(payment)
            logger.info(f"Платеж {payment.order_id} отмечен как неудачный")
            return JsonResponse({'success': True, 'message': 'Payment marked as failed'})
        
        else:
            return JsonResponse({'error': 'Invalid status'}, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Ошибка в webhook: {e}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


def publish_post_after_payment(payment):
    """Найти и опубликовать пост после успешной оплаты"""
    try:
        # Ищем последний пост пользователя в черновиках/на модерации
        post = AbsPost.objects.filter(
            user=payment.user,
            status=0,  # На модерации
            is_deleted=False
        ).order_by('-created_at').first()
        
        if post:
            # Публикуем пост с оплаченным тарифом
            if PostPublicationService.publish_post(post, payment.package, payment):
                logger.info(f"Пост {post.id} отправлен на модерацию после оплаты {payment.order_id}")
                return True
            else:
                logger.error(f"Не удалось опубликовать пост {post.id} после оплаты")
                return False
        else:
            logger.warning(f"Не найден пост для публикации после платежа {payment.order_id}")
            return False
            
    except Exception as e:
        logger.error(f"Ошибка публикации поста после оплаты {payment.order_id}: {e}")
        return False


@csrf_exempt  
@require_POST
def test_payment_webhook(request):
    """Тестовый webhook для проверки оплаты"""
    try:
        data = json.loads(request.body.decode('utf-8'))
        payment_id = data.get('payment_id')
        
        if not payment_id:
            return JsonResponse({'error': 'Missing payment_id'}, status=400)
            
        # Имитируем успешную оплату
        response_data = {
            'payment_id': payment_id,
            'status': 'paid',
            'telegram_payment_charge_id': 'test_charge_123',
            'provider_payment_charge_id': 'provider_123'
        }
        
        # Вызываем настоящий webhook
        import requests
        webhook_url = request.build_absolute_uri('/payments/webhook/simple/')
        
        webhook_response = requests.post(
            webhook_url,
            json=response_data,
            headers={'Content-Type': 'application/json'}
        )
        
        return JsonResponse({
            'test_success': True,
            'webhook_status': webhook_response.status_code,
            'webhook_response': webhook_response.json() if webhook_response.status_code == 200 else webhook_response.text
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)