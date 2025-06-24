"""
Views для обработки платежей
"""
import json
import logging
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext as _
from django.urls import reverse

from ework_premium.models import Payment, Package
from ework_payment.services import PaymentService, PostPublicationService, TelegramPaymentService

logger = logging.getLogger(__name__)


@login_required
@require_POST
def create_payment(request):
    """Создать платеж для выбранного тарифа"""
    try:
        data = json.loads(request.body)
        package_id = data.get('package_id')
        
        if not package_id:
            return JsonResponse({'error': 'Не указан ID тарифа'}, status=400)
        
        package = get_object_or_404(Package, id=package_id, is_active=True)
        
        # Проверяем, что тариф платный
        if package.is_free():
            return JsonResponse({'error': 'Для бесплатного тарифа не нужна оплата'}, status=400)
        
        # Создаем платеж
        payment = PaymentService.create_payment(request.user, package)
        
        # Создаем данные для Telegram invoice
        invoice_data = TelegramPaymentService.create_invoice_payload(payment)
        
        return JsonResponse({
            'success': True,
            'payment_id': payment.id,
            'order_id': payment.order_id,
            'amount': float(payment.amount),
            'currency': package.currency.code if package.currency else 'UAH',
            'invoice_data': invoice_data
        })
        
    except Exception as e:
        logger.error(f"Ошибка создания платежа: {e}")
        return JsonResponse({'error': 'Внутренняя ошибка сервера'}, status=500)


@csrf_exempt
@require_POST
def telegram_payment_callback(request):
    """Обработка callback от Telegram Payments"""
    try:
        data = json.loads(request.body)
        
        # Извлекаем данные из callback
        payment_charge_id = data.get('telegram_payment_charge_id')
        provider_charge_id = data.get('provider_payment_charge_id')
        payload = data.get('invoice_payload')
        
        if not payload:
            logger.error("Нет payload в callback от Telegram")
            return HttpResponse(status=400)
        
        # Извлекаем user_id и payment_id из payload
        try:
            user_id, payment_id = payload.split('&&&')
            payment = get_object_or_404(Payment, id=payment_id, user_id=user_id)
        except (ValueError, Payment.DoesNotExist):
            logger.error(f"Неверный payload: {payload}")
            return HttpResponse(status=400)
        
        # Проверяем данные платежа
        if not TelegramPaymentService.verify_payment(data):
            logger.error("Не удалось верифицировать платеж от Telegram")
            return HttpResponse(status=400)
        
        # Обрабатываем успешный платеж
        if PaymentService.process_successful_payment(payment, payment_charge_id, provider_charge_id):
            logger.info(f"Платеж {payment.order_id} успешно обработан")
            return HttpResponse(status=200)
        else:
            logger.error(f"Не удалось обработать платеж {payment.order_id}")
            return HttpResponse(status=500)
            
    except Exception as e:
        logger.error(f"Ошибка в callback от Telegram: {e}")
        return HttpResponse(status=500)


@login_required
def payment_status(request, payment_id):
    """Проверить статус платежа"""
    try:
        payment = get_object_or_404(Payment, id=payment_id, user=request.user)
        
        return JsonResponse({
            'status': payment.status,
            'amount': float(payment.amount),
            'currency': payment.package.currency.code if payment.package.currency else 'UAH',
            'created_at': payment.created_at.isoformat(),
            'paid_at': payment.paid_at.isoformat() if payment.paid_at else None
        })
        
    except Exception as e:
        logger.error(f"Ошибка проверки статуса платежа {payment_id}: {e}")
        return JsonResponse({'error': 'Ошибка проверки статуса'}, status=500)


@login_required
def payment_success(request, payment_id):
    """Страница успешной оплаты"""
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)
    
    if payment.status == 'paid':
        messages.success(request, _('Платеж успешно обработан!'))
    else:
        messages.warning(request, _('Платеж еще не обработан'))
    
    return redirect('core:home')


@login_required
def payment_cancel(request, payment_id):
    """Страница отмены платежа"""
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)
    
    if payment.status == 'pending':
        payment.status = 'cancelled'
        payment.save()
        messages.info(request, _('Платеж отменен'))
    
    return redirect('core:home')