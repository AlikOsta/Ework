from aiogram import Bot
import asyncio
import html


YOUR_PERSONAL_CHAT_ID = 7727039536

TELEGRAM_BOT_TOKEN = "7662590757:AAHpuX8hKUO8aCk3nGWsedA286qh0G0OAzw"


async def send_telegram_message(token, chat_id, message, parse_mode='HTML'):
    bot = Bot(token=token)
    try:
        if parse_mode == 'HTML':
            message = html.escape(message)
        
        await bot.send_message(chat_id=chat_id, text=message, parse_mode=parse_mode)
        print("Сообщение отправлено")
    except Exception as e:
        print(f"Ошибка при отправке сообщения: {e}")
    finally:
        await bot.session.close()
        print("Закрытие сессии")


if __name__ == "__main__":
    message = "Тестовое сообщение"
    asyncio.run(send_telegram_message(TELEGRAM_BOT_TOKEN, YOUR_PERSONAL_CHAT_ID, message))
