from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from aiogram import Bot
import asyncio
import time


@csrf_exempt
@require_POST
def create_payment(request):
    try:
        print("Payment request received")
        
        # Получаем конфигурацию
        from ework_config.utils import get_config
        config = get_config()
        
        # Фиксированные параметры платежа
        amount = 1000  # 10 рублей в копейках
        payload = f"post_creation_{int(time.time())}"
        
        async def create_invoice():
            async with Bot(token=config.bot_token) as bot:
                return await bot.create_invoice_link(
                    title="Размещение услуги",
                    description="Оплата за размещение услуги на платформе",
                    payload=payload,
                    provider_token=config.payment_provider_token,
                    currency="RUB",
                    prices=[{"label": "Размещение услуги", "amount": amount}],
                    need_email=False,
                    need_phone_number=False,
                    need_name=False
                )
        
        invoice_link = asyncio.run(create_invoice())
        print(f"Invoice link created: {invoice_link}")
        return JsonResponse({'invoice_link': invoice_link})
    
    except Exception as e:
        import traceback
        print(f"Error: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({'error': 'Internal server error'}, status=500)