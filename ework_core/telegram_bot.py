from aiogram import Bot
import asyncio
import html


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


async def send_telegram_message_with_keyboard(token, chat_id, message, keyboard, parse_mode='HTML'):
    """Отправляет сообщение в Telegram с inline клавиатурой"""
    bot = Bot(token=token)
    try:
        # НЕ экранируем HTML для сообщений с разметкой
        await bot.send_message(
            chat_id=chat_id, 
            text=message, 
            parse_mode=parse_mode,
            reply_markup=keyboard
        )
        print("Сообщение с клавиатурой отправлено")
    except Exception as e:
        print(f"Ошибка при отправке сообщения с клавиатурой: {e}")
    finally:
        await bot.session.close()
        print("Закрытие сессии")
