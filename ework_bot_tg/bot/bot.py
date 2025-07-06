import os
import django
import asyncio
import logging
from logging.handlers import RotatingFileHandler
from django.utils.translation import gettext as _ 

import httpx
from aiogram import Dispatcher, types
from aiogram.client.bot import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.types import (
    WebAppInfo,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LabeledPrice,
)
from asgiref.sync import sync_to_async


from ework_job.models import PostJob
from ework_services.models import PostServices

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ework.settings')
django.setup()

# Получаем конфигурацию бота
from ework_config.bot_config import get_bot_config
cfg = get_bot_config()

# Настройка логирования
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Файл с ротацией: до 5 файлов по 5 МБ
file_handler = RotatingFileHandler(
    filename='bot.log',
    maxBytes=5 * 1024 * 1024,
    backupCount=5,
    encoding='utf-8'
)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s | %(name)s | %(levelname)s | %(message)s'
))

# Консольный вывод
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter(
    '%(levelname)s %(message)s'
))

logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Инициализация бота и диспетчера
default_props = DefaultBotProperties(parse_mode="HTML")
bot = Bot(token=cfg['bot_token'], default=default_props)
welcome_text = """
Вас вітає Help Work🔎!

Кілька слів про наш проект👇
•  Зручність: Подавайте оголошення чи знаходьте роботу мрії в кілька кліків.
•  Безкоштовно: Розміщуйте оголошення або шукайте роботу без жодних витрат.
•  Великі охвати: Багато актуальних вакансій і широка аудиторія для ваших оголошень.
•  Без реєстрацій: Ніяких складних форм — усе просто і швидко.
💪 Для шукачів роботи: Легко переглядайте вакансії, відгукуйтесь і знаходьте ідеальну роботу!
📢 Для роботодавців: Розміщуйте вакансії та швидко знаходьте найкращих кандидатів!
Починайте вже зараз — це просто, зручно та ефективно!

📨 @HelpWorkUa
"""
text_button = "Открыть"

start_img = ""

dp = Dispatcher()

# Асинхронный HTTP-клиент (singleton)
_http_client: httpx.AsyncClient | None = None

def get_http_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(timeout=30.0)
    return _http_client

async def create_invoice_link(
    user_id: int,
    payment_id: int,
    payload: str,
    amount: float,
    order_id: int,
    addons_data: dict | None = None
) -> str | None:
    """
    Создать инвойс через HTTP API Telegram и вернуть ссылку
    """
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

    price_kopecks = int(amount * 100)
    data = {
        "title": "Публикация объявления",
        "description": description,
        "payload": payload,
        "provider_token": cfg['payment_provider_token'],
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
    url = f"https://api.telegram.org/bot{cfg['bot_token']}/createInvoiceLink"
    try:
        client = get_http_client()
        response = await client.post(url, json=data)
        response.raise_for_status()
        result = response.json()
        if result.get('ok'):
            return result['result']
        else:
            logger.error("Telegram API error creating invoice: %s", result)
    except Exception:
        logger.exception(
            "Failed to create invoice link for payment %s (user %s)",
            payment_id, user_id
        )
    return None

# Команда /start
@dp.message(Command(commands=["start"]))
async def cmd_start(message: types.Message):
    webapp_button = InlineKeyboardButton(
        text=text_button,
        web_app=WebAppInfo(url=cfg['miniapp_url'])
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[webapp_button]])

    await message.answer_photo(
        photo='https://ibb.co/3ms35B22',  
        caption=f"{welcome_text}",
        reply_markup=keyboard
    )


# Обработка коллбеков модерации - ИСПРАВЛЕННАЯ ВЕРСИЯ
@dp.callback_query(lambda c: c.data and (c.data.startswith('approve_post_') or c.data.startswith('reject_post_')))
async def handle_moderation_callback(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    callback_data = callback_query.data
    
    print(f"🔔 Получен коллбек: {callback_data} от пользователя {user_id}")
    
    try:
        # Парсим callback_data правильно
        if callback_data.startswith('approve_post_'):
            action = 'approve'
            post_id = callback_data.replace('approve_post_', '')
        elif callback_data.startswith('reject_post_'):
            action = 'reject'
            post_id = callback_data.replace('reject_post_', '')
        else:
            print(f"❌ Неизвестный callback_data: {callback_data}")
            await callback_query.answer("❌ Неизвестная команда", show_alert=True)
            return
        
        print(f"📊 Обработка: action={action}, post_id={post_id}")
        
        # Ищем пост в двух моделях
        post = None
        try:
            post = await sync_to_async(PostJob.objects.get)(id=int(post_id), status=1)  # На модерации
            print(f"📋 Найден пост-вакансия: {post.title}")
        except (PostJob.DoesNotExist, ValueError):
            try:
                post = await sync_to_async(PostServices.objects.get)(id=int(post_id), status=1)  # На модерации
                print(f"🛠️ Найден пост-услуга: {post.title}")
            except (PostServices.DoesNotExist, ValueError):
                print(f"❌ Пост с ID {post_id} не найден или не на модерации")
                await callback_query.answer("❌ Пост не найден или уже обработан", show_alert=True)
                return

        if action == 'approve':
            # Одобряем пост
            post.status = 3  # Опубликовано
            await sync_to_async(post.save)(update_fields=['status'])
            
            response_text = f"✅ Пост '{post.title}' одобрен и опубликован!"
            print(f"✅ Пост {post_id} одобрен и опубликован")
            
        elif action == 'reject':
            # Отклоняем пост
            post.status = 2  # Отклонено
            await sync_to_async(post.save)(update_fields=['status'])
            
            # Возвращаем деньги если пост был платным
            from ework_core.signals import refund_if_paid
            await sync_to_async(refund_if_paid)(post)
            
            response_text = f"❌ Пост '{post.title}' отклонен"
            print(f"❌ Пост {post_id} отклонен")

        # Редактируем сообщение вместо удаления
        try:
            await callback_query.message.edit_text(
                f"✅ Обработано!\n\n{response_text}",
                parse_mode="HTML"
            )
        except Exception as e:
            print(f"⚠️ Не удалось отредактировать сообщение: {e}")
            # Если не получилось отредактировать, удаляем
            try:
                await callback_query.message.delete()
            except:
                pass
        
        # Отправляем ответ
        await callback_query.answer(response_text, show_alert=True)
        
    except Exception as e:
        print(f"❌ Ошибка при обработке модерации: {e}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        await callback_query.answer("❌ Произошла ошибка при модерации", show_alert=True)



# Pre-checkout
@dp.pre_checkout_query()
async def pre_checkout_query(pre_checkout: types.PreCheckoutQuery):
    await pre_checkout.bot.answer_pre_checkout_query(
        pre_checkout_query_id=pre_checkout.id,
        ok=True
    )

# Успешная оплата
@dp.message(lambda msg: msg.successful_payment)
async def successful_payment(message: types.Message):
    payload = message.successful_payment.invoice_payload
    try:
        user_id_str, payment_id_str = payload.split('&&&')
        user_id, payment_id = int(user_id_str), int(payment_id_str)
        
        from ework_core.views import publish_post_after_payment
        success = await sync_to_async(publish_post_after_payment)(user_id, payment_id)
        
        if success:
            await message.answer(_("✅ Оплата прошла успешно! Ваше объявление опубликовано и отправлено на модерацию."))
        else:
            await message.answer(_("⚠️ Оплата получена, но при публикации произошла ошибка. Обратитесь в поддержку."))
    except Exception:
        logger.exception("Error handling successful payment payload=%s", payload)
        await message.answer(_("⚠️ Оплата получена, но произошла ошибка. Обратитесь в поддержку."))

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
