import asyncio
import os
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from dotenv import load_dotenv

from database import init_db
from handlers import router

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

async def main():
    # Инициализируем базу данных
    await init_db()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Подключаем роутер
    dp.include_router(router)

    # Устанавливаем кнопку меню (возле поля ввода текста)
    commands = [
        BotCommand(command="start", description="Запустить / перезапустить исследование")
    ]
    await bot.set_my_commands(commands)

    print("Бот запущен и готов к работе...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())