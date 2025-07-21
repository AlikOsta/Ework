from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.views import View
import json
import logging

from ework_premium.models import Payment

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class TelegramPaymentWebhookView(View):
    """Webhook для обработки платежей от Telegram"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            if 'pre_checkout_query' in data:
                return self.handle_pre_checkout(data['pre_checkout_query'])
            elif 'message' in data and 'successful_payment' in data['message']:
                return self.handle_successful_payment(data['message']['successful_payment'])
            else:
                logger.warning(f"Unknown webhook type: {data}")
                return HttpResponse(status=200)
                
        except Exception as e:
            logger.error(f"Error processing Telegram webhook: {e}")
            return JsonResponse({'error': 'Internal server error'}, status=500)
    
    def handle_pre_checkout(self, pre_checkout_query):
        """Обработка pre-checkout запроса"""
        try:
            payload = pre_checkout_query.get('invoice_payload', '')
            amount = pre_checkout_query.get('total_amount', 0)
            if '&&&' in payload:
                user_id, payment_id = payload.split('&&&')
                try:
                    payment = Payment.objects.get(id=payment_id, user_id=user_id)
                    expected_amount = int(payment.amount * 100)
                    if amount != expected_amount:
                        logger.error(f"Amount mismatch: expected {expected_amount}, got {amount}")
                        return JsonResponse({
                            'ok': False,
                            'error_message': 'Неверная сумма платежа'
                        })
                    return JsonResponse({'ok': True})
                    
                except Payment.DoesNotExist:
                    logger.error(f"Payment not found: {payment_id}")
                    return JsonResponse({
                        'ok': False,
                        'error_message': 'Платеж не найден'
                    })
            else:
                logger.error(f"Invalid payload format: {payload}")
                return JsonResponse({
                    'ok': False,
                    'error_message': 'Неверный формат платежа'
                })
                
        except Exception as e:
            logger.error(f"Error in pre_checkout: {e}")
            return JsonResponse({
                'ok': False,
                'error_message': 'Ошибка обработки платежа'
            })
    
    def handle_successful_payment(self, successful_payment):
        """Обработка успешного платежа"""
        try:
            payload = successful_payment.get('invoice_payload', '')
            telegram_charge_id = successful_payment.get('telegram_payment_charge_id')
            provider_charge_id = successful_payment.get('provider_payment_charge_id')
            if '&&&' in payload:
                user_id, payment_id = payload.split('&&&')
                
                try:
                    payment = Payment.objects.get(id=payment_id, user_id=user_id)
                    payment.mark_as_paid(
                        telegram_charge_id=telegram_charge_id,
                        provider_charge_id=provider_charge_id
                    )
                    return HttpResponse(status=200)
                    
                except Payment.DoesNotExist:
                    logger.error(f"Payment not found for successful payment: {payment_id}")
                    
            return HttpResponse(status=200)
            
        except Exception as e:
            logger.error(f"Error in successful_payment: {e}")
            return HttpResponse(status=500)


@csrf_exempt
@require_POST
def telegram_payment_webhook(request):
    """Простая функция-обработчик для webhook платежей"""
    view = TelegramPaymentWebhookView()
    return view.post(request)
