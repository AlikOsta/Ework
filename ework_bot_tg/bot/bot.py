from aiogram import Dispatcher, types
from aiogram.client.bot import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.types import WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
import asyncio

BOT_TOKEN = "7554067474:AAG75CqnZSiqKiWgpZ4zX6hNW_e6f9uZn1g"
MINIAPP_URL = "https://6e89-181-97-30-161.ngrok-free.app/users/index/"

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

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
