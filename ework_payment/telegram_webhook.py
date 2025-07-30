"""
Webhook для обработки платежей от Telegram Bot API
"""
import json
import logging
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.views import View
from ework_premium.models import Payment
from ework_payment.services import PaymentService, PostPublicationService
from ework_post.models import AbsPost

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class TelegramPaymentWebhook(View):
    """Webhook для обработки событий оплаты от Telegram"""
    
    def post(self, request):
        try:
            data = json.loads(request.body.decode('utf-8'))
            
            # Определяем тип события
            if 'successful_payment' in data.get('message', {}):
                return self.handle_successful_payment(data)
            elif 'pre_checkout_query' in data:
                return self.handle_pre_checkout_query(data)
            else:
                logger.info(f"Неизвестный тип webhook события: {data}")
                return HttpResponse(status=200)
                
        except Exception as e:
            logger.error(f"Ошибка обработки webhook: {e}")
            return HttpResponse(status=500)
    
    def handle_successful_payment(self, data):
        """Обработка успешного платежа"""
        try:
            message = data.get('message', {})
            successful_payment = message.get('successful_payment', {})
            
            # Извлекаем данные платежа
            payload = successful_payment.get('invoice_payload')
            telegram_payment_charge_id = successful_payment.get('telegram_payment_charge_id')
            provider_payment_charge_id = successful_payment.get('provider_payment_charge_id')
            
            if not payload:
                logger.error("Нет payload в successful_payment")
                return HttpResponse(status=400)
            
            # Парсим payload
            try:
                user_id, payment_id = payload.split('&&&')
                payment = Payment.objects.get(id=payment_id, user_id=user_id)
            except (ValueError, Payment.DoesNotExist):
                logger.error(f"Неверный payload или платеж не найден: {payload}")
                return HttpResponse(status=400)
            
            # Проверяем, что платеж еще не обработан
            if payment.status != 'pending':
                logger.warning(f"Платеж {payment.order_id} уже обработан")
                return HttpResponse(status=200)
            
            # Обрабатываем успешный платеж
            if PaymentService.process_successful_payment(
                payment, 
                telegram_payment_charge_id, 
                provider_payment_charge_id
            ):
                # Ищем пост, связанный с этим платежом, и публикуем его
                self.publish_paid_post(payment)
                
                logger.info(f"Успешно обработан платеж {payment.order_id}")
                return HttpResponse(status=200)
            else:
                logger.error(f"Не удалось обработать платеж {payment.order_id}")
                return HttpResponse(status=500)
                
        except Exception as e:
            logger.error(f"Ошибка в handle_successful_payment: {e}")
            return HttpResponse(status=500)
    
    def handle_pre_checkout_query(self, data):
        """Обработка pre-checkout запроса"""
        try:
            pre_checkout_query = data.get('pre_checkout_query', {})
            query_id = pre_checkout_query.get('id')
            payload = pre_checkout_query.get('invoice_payload')
            
            # Проверяем валидность payload
            try:
                user_id, payment_id = payload.split('&&&')
                payment = Payment.objects.get(id=payment_id, user_id=user_id, status='pending')
                
                # Если все в порядке, отвечаем успешно
                # В реальном приложении здесь был бы API вызов к Telegram Bot API
                logger.info(f"Pre-checkout query успешно обработан для платежа {payment.order_id}")
                return HttpResponse(status=200)
                
            except (ValueError, Payment.DoesNotExist):
                logger.error(f"Неверный payload в pre-checkout: {payload}")
                # В реальном приложении здесь был бы вызов answerPreCheckoutQuery с error_message
                return HttpResponse(status=400)
                
        except Exception as e:
            logger.error(f"Ошибка в handle_pre_checkout_query: {e}")
            return HttpResponse(status=500)
    
    def publish_paid_post(self, payment):
        """Найти и опубликовать пост после оплаты"""
        try:
            # Ищем последний пост пользователя в черновиках
            post = AbsPost.objects.filter(
                user=payment.user,
                status=0,  # На модерации/черновик
                is_deleted=False
            ).order_by('-created_at').first()
            
            if post:
                # Публикуем пост с оплаченным тарифом
                if PostPublicationService.publish_post(post, payment.package, payment):
                    logger.info(f"Пост {post.id} опубликован после оплаты {payment.order_id}")
                else:
                    logger.error(f"Не удалось опубликовать пост {post.id} после оплаты")
            else:
                logger.warning(f"Не найден пост для публикации после платежа {payment.order_id}")
                
        except Exception as e:
            logger.error(f"Ошибка публикации поста после оплаты {payment.order_id}: {e}")


# Функция-view для совместимости
@csrf_exempt
@require_POST
def telegram_payment_webhook(request):
    """Функция-обертка для webhook"""
    webhook = TelegramPaymentWebhook()
    return webhook.post(request)