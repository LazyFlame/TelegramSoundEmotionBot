import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from dotenv import load_dotenv
import database as db
from handlers import router as quiz_router

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
dp.include_router(quiz_router)


async def main():
    await db.init_db()

    print("Бот запущен успешно...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
