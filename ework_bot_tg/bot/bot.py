from aiogram import Dispatcher, types
from aiogram.client.bot import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.types import WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
import asyncio

# BOT_TOKEN and MINIAPP_URL moved to SiteConfig

# Функция для создания инвойс-ссылки
async def create_invoice_link_async(user_id, payment_id, payload, amount, order_id, addons_data):
    """Создать инвойс и вернуть ссылку"""
    try:
        # Получаем конфигурацию в начале функции
        from ework_config.bot_config import get_bot_config
        bot_config = get_bot_config()
        print(f"🔧 Создаем инвойс для платежа {payment_id}")
        print(f"🔧 User ID: {user_id}")
        print(f"🔧 Payment amount: {amount}")
        print(f"🔧 Payment order_id: {order_id}")
        print(f"🔧 Payment addons: {addons_data}")
        
        # Формируем описание платежа
        description = f"Публикация объявления #{order_id}"
        
        if addons_data:
            addons = []
            if addons_data.get('photo'):
                addons.append("Фото")
            if addons_data.get('highlight'):
                addons.append("Выделение")
            if addons_data.get('auto_bump'):
                addons.append("Автоподнятие")
            
            if addons:
                description += f" с опциями: {', '.join(addons)}"
        
        # Цена в копейках
        price_kopecks = int(float(amount) * 100)
        print(f"🔧 Price in kopecks: {price_kopecks}")
        print(f"🔧 Description: {description}")
        print(f"🔧 Payload: {payload}")
        print(f"🔧 Provider token: {bot_config['payment_provider_token']}")
        
        # Создаем инвойс ссылку
        print("🔧 Вызываем bot.create_invoice_link...")
        invoice_link = await bot.create_invoice_link(
            title="Публикация объявления",
            description=description,
            payload=payload,
            provider_token=bot_config['payment_provider_token'],
            currency="RUB",
            prices=[
                LabeledPrice(label="Публикация объявления", amount=price_kopecks)
            ],
            need_name=False,
            need_phone_number=False,
            need_email=False,
            need_shipping_address=False,
            send_phone_number_to_provider=False,
            send_email_to_provider=False,
            is_flexible=False,
        )
        
        print(f"✅ Инвойс создан для платежа {payment_id}: {invoice_link}")
        return invoice_link
        
    except Exception as e:
        print(f"❌ Ошибка создания инвойса для платежа {payment_id}: {e}")
        print(f"❌ Тип ошибки: {type(e)}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        return None

def create_invoice_link(user_id, payment_id, payload, amount, order_id, addons_data):
    """Создать инвойс через HTTP API"""
    import requests
    
    try:
        print(f"🔧 HTTP метод: создаем инвойс для payment {payment_id}")
        
        # Формируем описание платежа
        description = f"Публикация объявления #{order_id}"
        
        if addons_data:
            addons = []
            if addons_data.get('photo'):
                addons.append("Фото")
            if addons_data.get('highlight'):
                addons.append("Выделение")
            if addons_data.get('auto_bump'):
                addons.append("Автоподнятие")
            
            if addons:
                description += f" с опциями: {', '.join(addons)}"
        
        # Цена в копейках
        price_kopecks = int(float(amount) * 100)
        
        print(f"🔧 Отправляем HTTP запрос к Telegram Bot API...")
        print(f"🔧 Amount: {amount} руб = {price_kopecks} коп")
        print(f"🔧 Description: {description}")
        
        # HTTP запрос к Telegram Bot API
        from ework_config.bot_config import get_bot_config
        bot_config = get_bot_config()
        url = f"https://api.telegram.org/bot{bot_config['bot_token']}/createInvoiceLink"
        
        data = {
            "title": "Публикация объявления",
            "description": description,
            "payload": payload,
            "provider_token": bot_config['payment_provider_token'],
            "currency": "RUB",
            "prices": [{"label": "Публикация объявления", "amount": price_kopecks}],
            "need_name": False,
            "need_phone_number": False,
            "need_email": False,
            "need_shipping_address": False,
            "send_phone_number_to_provider": False,
            "send_email_to_provider": False,
            "is_flexible": False,
        }
        
        response = requests.post(url, json=data, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        
        if result.get('ok'):
            invoice_link = result.get('result')
            print(f"✅ HTTP: Инвойс создан для платежа {payment_id}: {invoice_link}")
            return invoice_link
        else:
            print(f"❌ HTTP: Ошибка от Telegram: {result}")
            return None
        
    except Exception as e:
        print(f"❌ HTTP: Ошибка создания инвойса: {e}")
        import traceback
        print(f"❌ HTTP: Traceback: {traceback.format_exc()}")
        return None
# Получаем конфигурацию
from ework_config.bot_config import get_bot_config
bot_config = get_bot_config()

# Указываем parse_mode через DefaultBotProperties
default_props = DefaultBotProperties(parse_mode="HTML")
bot = Bot(token=bot_config['bot_token'], default=default_props)
dp = Dispatcher()

print(f"🤖 Bot инициализирован с токеном: {bot_config['bot_token'][:10]}...")
print(f"🔑 Provider token: {bot_config['payment_provider_token'][:10]}...")

@dp.message(Command(commands=["start"]))
async def cmd_start(message: types.Message):
    """
    Хендлер для команды /start: отправляет кнопку для открытия Mini App
    """
    webapp_button = InlineKeyboardButton(
        text="🚀 Открыть Mini App",
        web_app=WebAppInfo(url=bot_config['miniapp_url'])
    )
    # Собираем клавиатуру
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[webapp_button]])

    await message.answer(
        text="Привет! Нажми на кнопку ниже, чтобы открыть наш Mini App:",
        reply_markup=keyboard
    )

@dp.callback_query(lambda c: c.data.startswith('approve_post_') or c.data.startswith('reject_post_'))
async def handle_moderation_callback(callback_query: types.CallbackQuery):
    """Обработка кнопок модерации постов"""
    try:
        action = callback_query.data.split('_')[0]  # approve или reject
        post_id = callback_query.data.split('_')[2]  # ID поста
        
        print(f"🔧 Получен callback модерации: {action} для поста {post_id}")
        
        # Импортируем модели Django
        import os
        import django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ework.settings')
        django.setup()
        
        from ework_job.models import PostJob
        from ework_services.models import PostServices
        
        # Ищем пост в обеих моделях (на модерации)
        post = None
        try:
            post = PostJob.objects.get(id=post_id, status=1)  # На модерации
        except PostJob.DoesNotExist:
            try:
                post = PostServices.objects.get(id=post_id, status=1)
            except PostServices.DoesNotExist:
                await callback_query.answer("❌ Пост не найден или уже обработан", show_alert=True)
                return
        
        if action == 'approve':
            post.status = 3  # Опубликовано
            post.save()
            response_text = f"✅ Пост '{post.title}' одобрен и опубликован!"
            
            # Отправляем уведомление о публикации
            from ework_core.signals import send_telegram_notification_async
            send_telegram_notification_async(post)
            
        elif action == 'reject':
            post.status = 2  # Отклонено
            post.save()
            response_text = f"❌ Пост '{post.title}' отклонен"
            
            # Возвращаем деньги если был платным
            from ework_core.signals import refund_if_paid
            refund_if_paid(post)
        
        # Удаляем сообщение из чата
        await callback_query.message.delete()
        
        await callback_query.answer(response_text, show_alert=True)
        
    except Exception as e:
        print(f"❌ Ошибка обработки модерации: {e}")
        await callback_query.answer("❌ Произошла ошибка", show_alert=True)

@dp.message(Command(commands=["invoice"]))
async def send_invoice(message: types.Message):
    await message.bot.send_invoice(
        chat_id=message.chat.id,
        title="Название товара",
        description="Описание товара",
        payload="unique_payload",
        provider_token=bot_config['payment_provider_token'],
        currency="RUB",
        prices=[
            LabeledPrice(label="Товар", amount=1000),  # 10.00 рублей (в копейках)
        ],
        start_parameter="start_parameter",
        need_email=True,
    )

@dp.pre_checkout_query()
async def pre_checkout_query(pre_checkout: types.PreCheckoutQuery):
    await pre_checkout.bot.answer_pre_checkout_query(
        pre_checkout_query_id=pre_checkout.id,
        ok=True
    )

@dp.message(lambda message: message.successful_payment)
async def successful_payment(message: types.Message):
    """Обработка успешной оплаты"""
    payload = message.successful_payment.invoice_payload
    print(f"💰 Получена успешная оплата! Payload: {payload}")
    print(f"💰 Сумма: {message.successful_payment.total_amount/100} руб")
    print(f"💰 ID платежа Telegram: {message.successful_payment.telegram_payment_charge_id}")
    
    try:
        # Извлекаем user_id и payment_id из payload 
        user_id, payment_id = payload.split('&&&')
        user_id = int(user_id)
        payment_id = int(payment_id)
        
        print(f"💰 Обрабатываем платеж: user_id={user_id}, payment_id={payment_id}")
        
        # Вызываем Django API для публикации поста
        from ework_core.views import publish_post_after_payment
        from asgiref.sync import sync_to_async
        
        publish_post_sync = sync_to_async(publish_post_after_payment)
        success = await publish_post_sync(user_id, payment_id)
        
        if success:
            await message.answer("✅ Оплата прошла успешно! Ваше объявление опубликовано и отправлено на модерацию.")
        else:
            await message.answer("⚠️ Оплата получена, но произошла ошибка при публикации. Обратитесь в поддержку.")
            
    except Exception as e:
        print(f"❌ Ошибка обработки платежа: {e}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        await message.answer("⚠️ Оплата получена, но произошла ошибка. Обратитесь в поддержку.")

async def main():
    # Удаляем webhook перед запуском polling
    await bot.delete_webhook(drop_pending_updates=True)
    print("Webhook удален, запускаем polling...")

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
