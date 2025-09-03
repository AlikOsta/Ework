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
from ework_post.models import AbsPost

logger = logging.getLogger(__name__)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ework.settings')

from ework_config.bot_config import get_bot_config
cfg = get_bot_config()

admin_chat = cfg['admin_chat_id']

default_props = DefaultBotProperties(parse_mode="HTML")
bot = Bot(token=cfg['bot_token'], default=default_props)
dp = Dispatcher()


@dp.message(Command(commands=["start"]))
async def cmd_start(message: types.Message):
    webapp_button = InlineKeyboardButton(
        text=_('Открыть'),
        web_app=WebAppInfo(url=cfg['miniapp_url'])
    )
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[webapp_button]]
    )
    photo = 'https://i.ibb.co/vCwQnC3D/photo-2025-07-05-23-14-52.jpg'

    await message.answer_photo(
        photo=photo,
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


def send_admin_approval_notification(instance):
    """Отправка уведомления админам с кнопками одобрения/отклонения"""
    try:
        message = f"""
🔍 <b>Требуется модерация поста!</b>

📝 <b>Название:</b> {instance.title}
📄 <b>Описание:</b> {instance.description}

📂 <b>Категория:</b> {instance.sub_rubric.super_rubric.name}
📁 <b>Подкатегория:</b> {instance.sub_rubric.name}

💰 <b>Цена:</b> {instance.price} {instance.currency.code}
🏙️ <b>Город:</b> {instance.city.name}

👤 <b>Автор:</b> @{getattr(instance.user, 'username', 'неизвестен')}
        """.strip()

        chat_id =  admin_chat
        photo_url = (
            f"https://helpwork.com.ua{instance.image.url}"
            if instance.image
            else "https://i.ibb.co/fYD6Qgkg/photo-2025-08-19-18-08-57.jpg"
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Одобрить",
                    callback_data=f"approve_post_{instance.id}"
                ),
                InlineKeyboardButton(
                    text="❌ Отклонить",
                    callback_data=f"reject_post_{instance.id}"
                )
            ]
        ])

        async_to_sync(send_telegram_message_chat)(chat_id, message, photo_url, keyboard)

    except Exception as e:
        logger.error(f"❌ Ошибка при отправке админ-уведомления : {e}")




def send_telegram_city_chat(instance):
    try:
        if not instance.city or not instance.city.chat_id:
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

        chat_id =  instance.city.chat_id
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
        logger.error(f"❌ Ошибка при отправке уведомления: {e}")




async def send_telegram_message_chat(chat_id, message, photo_url, keyboard):
    
    try:
        await bot.send_photo(
            chat_id=chat_id,
            photo=photo_url,
            caption=message,
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"❌ Ошибка при отправке уведомления целевой чат: {e}")


@dp.callback_query(lambda c: c.data and (c.data.startswith('approve_post_') or c.data.startswith('reject_post_')))
async def handle_moderation_callback(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
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
            post = await sync_to_async(AbsPost.objects.get)(id=int(post_id), status=1)  # На модерации
        except (AbsPost.DoesNotExist, ValueError):
            logger.warning("Пост не найден или уже обработан")
            await callback_query.answer("❌ Пост не знайдений або вже оброблений", show_alert=True)
            return

        if action == 'approve':
            post.status = 3  # Опубликовано
            await sync_to_async(post.save)(update_fields=['status'])
            
            send_telegram_city_chat(post)
            
            response_text = f"✅ Пост '{post.title}' одобрен и опубликован!"
            
        elif action == 'reject':
            post.status = 2  # Отклонено
            await sync_to_async(post.save)(update_fields=['status'])
            
            response_text = f"❌ Пост '{post.title}' отклонен"
        try:
            await callback_query.message.edit_text(
                f"✅ Обработано!\n\n{response_text}",
                parse_mode="HTML"
            )
        except Exception as e:
            try:
                await callback_query.message.delete()
            except:
                pass
        
        # Отправляем ответ
        await callback_query.answer(response_text, show_alert=True)
        
    except Exception as e:
        logger.exception("Ошибка при обработке коллбека модерации: %s", e)
        await callback_query.answer("❌ Сталася помилка під час модерації", show_alert=True)



# Pre-checkout
# @dp.pre_checkout_query()
# async def pre_checkout_query(pre_checkout: types.PreCheckoutQuery):
#     await pre_checkout.bot.answer_pre_checkout_query(
#         pre_checkout_query_id=pre_checkout.id,
#         ok=True
#     )


# @dp.message(lambda msg: msg.successful_payment)
# async def successful_payment(message: types.Message):
#     payload = message.successful_payment.invoice_payload
#     try:
#         user_id_str, payment_id_str = payload.split('&&&')
#         user_id, payment_id = int(user_id_str), int(payment_id_str)
#         
#         from ework_core.views import publish_post_after_payment
#         success = await sync_to_async(publish_post_after_payment)(user_id, payment_id)
#         
#         if success:
#             await message.answer(_("✅ Оплата пройшла успішно! Ваше оголошення опубліковано та надіслано на модерацію."))
#         else:
#             await message.answer(_("⚠️ Оплату отримано, але при публікації сталася помилка. Зверніться на підтримку."))
#     except Exception:
#         logger.exception("Error handling successful payment payload=%s", payload)
#         await message.answer(_("⚠️ Оплату отримано, але сталася помилка. Зверніться на підтримку."))


# Асинхронный HTTP-клиент (singleton)
# _http_client: httpx.AsyncClient | None = None

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
