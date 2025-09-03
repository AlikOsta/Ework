import os
import asyncio
import logging
from django.utils.translation import gettext as _ 
from aiogram import Dispatcher, types
from aiogram.client.bot import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.types import WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from asgiref.sync import sync_to_async, async_to_sync

# from ework_post.models import AbsPost

logger = logging.getLogger(__name__)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ework.settings')

from ework_config.bot_config import get_bot_config

cfg = get_bot_config()

default_props = DefaultBotProperties(parse_mode="HTML")

bot = Bot(token=cfg['bot_token'], default=default_props)
dp = Dispatcher()

def_photo = 'https://i.ibb.co/vCwQnC3D/photo-2025-07-05-23-14-52.jpg'

@dp.message(Command(commands=["start"]))
async def cmd_start(message: types.Message):
    """Обработчик события /start"""
    webapp_button = InlineKeyboardButton(
        text="Відкрити",
        web_app=WebAppInfo(url=cfg['miniapp_url'])
    )
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[webapp_button]]
    )

    await message.answer_photo(
        photo=def_photo,
        caption = _("""Вас вітає Help Work🔎!

Кілька слів про наш проект👇
•  Зручність: Подавайте оголошення чи знаходьте роботу мрії в кілька кліків.
•  Безкоштовно: Розміщуйте оголошення або шукайте роботу без жодних витрат.
•  Великі охвати: Багато актуальних вакансій і широка аудиторія для ваших оголошень.
•  Без реєстрацій: Ніяких складних форм — усе просто і швидко.
💪 Для шукачів роботи: Легко переглядайте вакансії, відгукуйтесь і знаходьте ідеальну роботу!
📢 Для роботодавців: Розміщуйте вакансії та швидко знаходьте найкращих кандидатів!
Починайте вже зараз — це просто, зручно та ефективно!

📨 @HelpWorkUa"""),
        reply_markup=keyboard
    )


async def send_telegram_error_mes(message):
   chat_id = cfg['admin_chat_id']
   await bot.send_message(chat_id=chat_id, text=message)


async def send_telegram_message_chat(chat_id, message, photo_url, keyboard):
    """Отправка постов в чат и админ_чат"""
    try:
        await bot.send_photo(
            chat_id=chat_id,
            photo=photo_url,
            caption=message,
            reply_markup=keyboard
        )
    except Exception as e:
        async_to_sync(send_telegram_error_mes)(text = f"❌ Ошибка при отправке уведомления целевой чат: {e}")
        logger.error(f"❌ Ошибка при отправке уведомления целевой чат: {e}")


def send_telegram_city_chat(instance):
    """Отправка поста в целевую группу Города"""
    try:
        if not instance.city or not instance.city.chat_id:
            async_to_sync(send_telegram_error_mes)(text = f"❌ Не удалось отправить сообщение в чат города: у поста {instance.id} отсутствует город или chat_id.")
            logger.warning(f"❌ Не удалось отправить сообщение в чат города: у поста {instance.id} отсутствует город или chat_id.")
            return

        message = (f"""
📝 <b>Назва:</b> {instance.title}
📄 <b>Опис:</b> {instance.description}

📂 <b>Категорія:</b> {instance.sub_rubric.super_rubric.name}
📁 <b>Підкатегорія:</b> {instance.sub_rubric.name}

💰 <b>Ціна:</b> {instance.price} {instance.currency.code}
🏙️ <b>Місто:</b> {instance.city.name} - {instance.address}
        """.strip())

        chat_id = instance.city.chat_id
        photo_url = (
            f"https://helpwork.com.ua{instance.image.url}"
            if instance.image
            else "https://i.ibb.co/fYD6Qgkg/photo-2025-08-19-18-08-57.jpg"
        )

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Відкрити", url=f"{cfg['miniapp_url']}{instance.get_absolute_url()}")]
            ]
        )

        async_to_sync(send_telegram_message_chat)(chat_id, message, photo_url, keyboard)

    except Exception as e:
        async_to_sync(send_telegram_error_mes)(text = f"❌ Ошибка при отправке уведомления: {e}")
        logger.error(f"❌ Ошибка при отправке уведомления: {e}")




# def send_admin_approval_notification(instance):
#     """Отправка уведомления админам с кнопками одобрения/отклонения"""
#     try:
#         message = f"""
# 🔍 <b>Требуется модерация поста!</b>

# 📝 <b>Название:</b> {instance.title}
# 📄 <b>Описание:</b> {instance.description[:200]}{'...' if len(instance.description) > 200 else ''}
# 📂 <b>Категория:</b> {instance.sub_rubric.super_rubric.name}
# 📁 <b>Подкатегория:</b> {instance.sub_rubric.name}
# 💰 <b>Цена:</b> {instance.price} {instance.currency.code}
# 🏙️ <b>Город:</b> {instance.city.name}
# 👤 <b>Автор:</b> @{getattr(instance.user, 'username', 'неизвестен')}
#         """.strip()

#         keyboard = InlineKeyboardMarkup(inline_keyboard=[
#             [
#                 InlineKeyboardButton(
#                     text="✅ Одобрить",
#                     callback_data=f"approve_post_{instance.id}"
#                 ),
#                 InlineKeyboardButton(
#                     text="❌ Отклонить",
#                     callback_data=f"reject_post_{instance.id}"
#                 )
#             ]
#         ])

#         send_telegram_message_with_keyboard(message, keyboard)
#     except Exception as e:
#         logger.error(f"❌ Ошибка при отправке уведомления о модерации: {e}")


# def send_telegram_notification_async(instance):
#     try:
#         message = f"""
# Объявление {instance.id}:
# 📝 <b>Название:</b> {instance.title}
# 📄 <b>Описание:</b> {instance.description[:200]}{'...' if len(instance.description) > 200 else ''}
# 📂 <b>Категория:</b> {instance.sub_rubric.super_rubric.name}
# 📁 <b>Подкатегория:</b> {instance.sub_rubric.name}
# 💰 <b>Цена:</b> {instance.price} {instance.currency.code}
# 🏙️ <b>Город:</b> {instance.city.name}
# 👤 <b>Автор:</b> @{getattr(instance.user, 'username', 'неизвестен')}
#         """.strip()
        
#         send_telegram_message(message)

#     except Exception as e:
#         logger.error(f"❌ Ошибка при отправке уведомления: {e}")







# # Асинхронный HTTP-клиент (singleton)
# _http_client: httpx.AsyncClient | None = None

# def get_http_client() -> httpx.AsyncClient:
#     global _http_client
#     if _http_client is None:
#         _http_client = httpx.AsyncClient(timeout=30.0)
#     return _http_client
# def get_http_client() -> httpx.AsyncClient:
#     global _http_client
#     if _http_client is None:
#         _http_client = httpx.AsyncClient(timeout=30.0)
#     return _http_client


# Этап 6: Генерация ссылки на оплату
# async def create_invoice_link( user_id: int, payment_id: int, payload: str, amount: float, order_id: int, addons_data: dict | None = None) -> str | None:
#     """
#     Создать инвойс через HTTP API Telegram и вернуть ссылку
#     """
#     description = f"Публікація оголошення #{order_id}"
#     if addons_data:
#         addons = []
#         if addons_data.get('photo'):
#             addons.append("Фото")
#         if addons_data.get('highlight'):
#             addons.append("Виділення")
#         if addons:
#             description += f" з опціями: {', '.join(addons)}"

#     price_kopecks = int(amount * 100)
#     data = {
#         "title": "Публікація оголошення",
#         "description": description,
#         "payload": payload,
#         "provider_token": cfg['payment_provider_token'],
#         "currency": "UAH", # заменить валюту
#         "prices": [{"label": "Публікація оголошення", "amount": price_kopecks}],
#         "need_name": False,
#         "need_phone_number": False,
#         "need_email": False,
#         "need_shipping_address": False,
#         "send_phone_number_to_provider": False,
#         "send_email_to_provider": False,
#         "is_flexible": False,
#     }
#     url = f"https://api.telegram.org/bot{cfg['bot_token']}/createInvoiceLink"
#     try:
#         client = get_http_client()
#         response = await client.post(url, json=data)
#         response.raise_for_status()
#         result = response.json()
#         if result.get('ok'):
#             return result['result']
#         else:
#             logger.error("Telegram API error creating invoice: %s", result)
#     except Exception:
#         logger.exception(
#             "Failed to create invoice link for payment %s (user %s)",
#             payment_id, user_id
#         )
#     return None



async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)



if __name__ == "__main__":
    asyncio.run(main())
