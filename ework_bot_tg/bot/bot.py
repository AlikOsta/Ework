from aiogram import Dispatcher, types
from aiogram.client.bot import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.types import WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
import asyncio

BOT_TOKEN = "7554067474:AAG75CqnZSiqKiWgpZ4zX6hNW_e6f9uZn1g"
MINIAPP_URL = "https://6e89-181-97-30-161.ngrok-free.app/users/index/"
PAYMENT_PROVIDER_TOKEN = '1744374395:TEST:703d48b8cac170d51296'

# Указываем parse_mode через DefaultBotProperties
default_props = DefaultBotProperties(parse_mode="HTML")
bot = Bot(token=BOT_TOKEN, default=default_props)
dp = Dispatcher()

@dp.message(Command(commands=["start"]))
async def cmd_start(message: types.Message):
    """
    Хендлер для команды /start: отправляет кнопку для открытия Mini App
    """
    webapp_button = InlineKeyboardButton(
        text="🚀 Открыть Mini App",
        web_app=WebAppInfo(url=MINIAPP_URL)
    )
    # Собираем клавиатуру
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[webapp_button]])

    await message.answer(
        text="Привет! Нажми на кнопку ниже, чтобы открыть наш Mini App:",
        reply_markup=keyboard
    )

@dp.message(Command(commands=["invoice"]))
async def send_invoice(message: types.Message):
    await message.bot.send_invoice(
        chat_id=message.chat.id,
        title="Название товара",
        description="Описание товара",
        payload="unique_payload",
        provider_token=PAYMENT_PROVIDER_TOKEN,
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

async def successful_payment(message: types.Message):
    payload = message.successful_payment.invoice_payload
    user_id = int(payload.split('_')[1])
    
    # Здесь должна быть логика сохранения услуги в БД
    # Используйте payload для связи с данными из сессии
    
    await message.answer(f"✅ Оплата прошла успешно! Ваша услуга опубликована.")

async def main():
    # Удаляем webhook перед запуском polling
    await bot.delete_webhook(drop_pending_updates=True)
    print("Webhook удален, запускаем polling...")

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
