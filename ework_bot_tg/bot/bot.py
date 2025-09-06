import os
import asyncio
import logging
from django.utils.translation import gettext as _ 
from aiogram import Dispatcher, types
from aiogram.client.bot import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.types import WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from ework_job.models import PostJob
from ework_services.models import PostServices
from asgiref.sync import sync_to_async

from logger_config import logger


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ework.settings')

from ework_config.bot_config import get_bot_config

cfg = get_bot_config()

default_props = DefaultBotProperties(parse_mode="HTML")

main_loop = asyncio.get_event_loop()

bot = Bot(token=cfg['bot_token'], default=default_props)
dp = Dispatcher()

def_photo = 'https://i.ibb.co/vCwQnC3D/photo-2025-07-05-23-14-52.jpg'


@dp.message(Command(commands=["start"]))
async def cmd_start(message: types.Message):
    """Обработчик события /start"""

    cfg = get_bot_config()

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
    try:
        cfg = get_bot_config()
        chat_id = cfg['admin_chat_id']
        await bot.send_message(chat_id=chat_id, text=message)
    except Exception as e:
       logger.error(f"Ошибка отправки сообщения с ошибкой админу. {e}")


async def send_telegram_city_chat(data):
    """Отправка поста в целевую группу Города"""
    try:
        message = (f"""
📝 <b>Назва:</b> {data["title"]}
🗒️ <b>Опис:</b> {data["description"]}

📂 <b>Категорія:</b> {data['sub_rubric']}
📍 <b>Місто:</b> {data['city']} {data['address']}
💰 <b>UAH:</b> {data['price']}
👤 <b>Користувач:</b> @{data['username']}
        """.strip())

        if data['username']:
            message += f"\n📱 <b>Телефон:</b> {data['phone_user']}"

        chat_id = data['city_chat_id']
        photo_url = (def_photo)

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Відкрити", url=f"t.me/HelpWorkUaBoT")]
            ]
        )
        try:
            await bot.send_photo(chat_id=chat_id, photo=photo_url, caption=message, reply_markup=keyboard)
        except Exception as e:
            logger.error(f"❌ Ошибка при отправке сообщения: {e}")

    except Exception as e:
        logger.error(f"❌ Ошибка при отправке уведомления: {e}")



async def send_admin_approval_notification(data):
    """Отправка уведомления админам с кнопками одобрения/отклонения"""
    try:
        message = (f"""
📝 <b>Назва:</b> {data["title"]}
🗒️ <b>Опис:</b> {data["description"]}

📂 <b>Категорія:</b> {data['sub_rubric']}
📍 <b>Місто:</b> {data['city']} {data['address']}
💰 <b>UAH:</b> {data['price']}
👤 <b>Користувач:</b> @{data['username']}
        """.strip())

        if data['username']:
            message += f"\n📱 <b>Телефон:</b> {data['phone_user']}"

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton( text="✅ Одобрить", callback_data=f"approve_post_{data['post_id']}"),
                InlineKeyboardButton( text="❌ Отклонить", callback_data=f"reject_post_{data['post_id']}")
            ]
        ])
        try:
            cfg = get_bot_config()

            chat_id = cfg['admin_chat_id']
            photo_url = (def_photo)
        
            await bot.send_photo(chat_id=chat_id, photo=photo_url, caption=message, reply_markup=keyboard)
        except Exception as e:
            logger.error(f"❌ Ошибка при отправке сообщения о модерации: {e}")

    except Exception as e:
        logger.error(f"❌ Ошибка при отправке уведомления о модерации: {e}")


@dp.callback_query(lambda c: c.data and (c.data.startswith('approve_post_') or c.data.startswith('reject_post_')))
async def handle_moderation_callback(callback_query: types.CallbackQuery):
    callback_data = callback_query.data
    try:
        if callback_data.startswith('approve_post_'):
            action = 'approve'
            post_id = callback_data.replace('approve_post_', '')
        elif callback_data.startswith('reject_post_'):
            action = 'reject'
            post_id = callback_data.replace('reject_post_', '')
        else:
            logger.warning("Неизвестная команда: %s", callback_data)
            await callback_query.answer("❌ Невідома команда", show_alert=True)
            return
        post = None
        try:
            post = await sync_to_async(PostJob.objects.get)(id=int(post_id))
        except (PostJob.DoesNotExist, ValueError):
            try:
                post = await sync_to_async(PostServices.objects.get)(id=int(post_id))
            except (PostServices.DoesNotExist, ValueError) as e:
                logger.warning("Пост не найден или уже обработан")
                await callback_query.answer(f"❌ Пост не знайдений або вже оброблений стр 184", show_alert=True)
                return

        if action == 'approve':
            post.status = 3  # Опубликовано
            await sync_to_async(post.save)(update_fields=['status'])

            async def get_post_data(post):
                def _extract():
                    return {
                        "post_id": post.id,
                        "title": post.title,
                        "description": post.description,
                        "price": post.price,
                        "sub_rubric": post.sub_rubric.name, 
                        "city": post.city.name,              
                        "address": post.address if post.address else "",
                        "username": post.user.username,
                        "phone_user": post.user_phone,
                        "city_chat_id": post.city.chat_id if post.city else cfg['admin_chat_id'],
                    }
                return await sync_to_async(_extract, thread_sensitive=True)()
            
            data = await get_post_data(post)
            await send_telegram_city_chat(data)
            
        elif action == 'reject':
            post.status = 2 
            await sync_to_async(post.save)(update_fields=['status'])
            
        await callback_query.message.delete()
        
    except Exception as e:
        logger.exception("Ошибка при обработке коллбека модерации: %s", e)
        await callback_query.answer("❌ Сталася помилка під час модерації", show_alert=True)




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
    logger.info("Запуск бота")



if __name__ == "__main__":
    asyncio.run(main())
