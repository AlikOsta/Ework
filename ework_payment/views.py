# """
# Views для обработки платежей
# """
# from django.utils.translation import gettext_lazy as _
# import json
# import logging
# from pyexpat.errors import messages
# from django.http import JsonResponse, HttpResponse
# from django.shortcuts import get_object_or_404, redirect
# from django.views.decorators.csrf import csrf_exempt
# from django.views.decorators.http import require_POST
# from aiogram import Bot
# import asyncio
# import time
# from asgiref.sync import sync_to_async

# from ework_premium.models import Payment

# logger = logging.getLogger(__name__)


# @csrf_exempt
# @require_POST
# def create_payment(request):
#     try:
#         print("Payment request received")
        
#         # Получаем конфигурацию
#         from ework_config.utils import get_config
#         config = get_config()
        
#         # Фиксированные параметры платежа
#         amount = 1000  # 10 рублей в копейках
#         payload = f"post_creation_{int(time.time())}"
        
#         async def create_invoice():
#             async with Bot(token=config.bot_token) as bot:
#                 return await bot.create_invoice_link(
#                     title="Размещение услуги",
#                     description="Оплата за размещение услуги на платформе",
#                     payload=payload,
#                     provider_token=config.payment_provider_token,
#                     currency="RUB",
#                     prices=[{"label": "Размещение услуги", "amount": amount}],
#                     need_email=False,
#                     need_phone_number=False,
#                     need_name=False
#                 )
        
#         invoice_link = asyncio.run(create_invoice())
#         print(f"Invoice link created: {invoice_link}")
#         return JsonResponse({'invoice_link': invoice_link})
    
#     except Exception as e:
#         logger.error(f"Ошибка проверки статуса платежа: {e}")
#         return JsonResponse({'error': 'Ошибка проверки статуса'}, status=500)


# def payment_success(request, payment_id):
#     """Страница успешной оплаты"""
#     payment = get_object_or_404(Payment, id=payment_id, user=request.user)
    
#     if payment.status == 'paid':
#         messages.success(request, _('Платеж успешно обработан!'))
#     else:
#         messages.warning(request, _('Платеж еще не обработан'))
    
#     return redirect('core:home')



# def payment_cancel(request, payment_id):
#     """Страница отмены платежа"""
#     payment = get_object_or_404(Payment, id=payment_id, user=request.user)
    
#     if payment.status == 'pending':
#         payment.status = 'cancelled'
#         payment.save()
#         messages.info(request, _('Платеж отменен'))
    
#     return redirect('core:home')