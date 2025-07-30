from aiogram import Bot
import html

import logging

logging.basicConfig(level=logging.ERROR)


async def send_telegram_message(token, chat_id, message, parse_mode='HTML'):
    bot = Bot(token=token)
    try:
        if parse_mode == 'HTML':
            message = html.escape(message)
        await bot.send_message(chat_id=chat_id, text=message, parse_mode=parse_mode)
    except Exception as e:
        logging.error(f"Ошибка при отправке сообщения: {e}")
    finally:
        await bot.session.close()



async def send_telegram_message_with_keyboard(token, chat_id, message, keyboard, parse_mode='HTML'):
    """Отправляет сообщение в Telegram с inline клавиатурой"""
    bot = Bot(token=token)
    try:
        await bot.send_message(
            chat_id=chat_id, 
            text=message, 
            parse_mode=parse_mode,
            reply_markup=keyboard
        )
    except Exception as e:
        logging.error(f"Ошибка при отправке сообщения: {e}")
    finally:
        await bot.session.close()
