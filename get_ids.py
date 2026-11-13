import asyncio
import os
from aiogram import Bot, Dispatcher, types
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message()
async def catch_file(message: types.Message):
    # Проверяем, есть ли в сообщении документ или аудиофайл
    file_id = None
    file_name = "неизвестно"

    if message.audio:
        file_id = message.audio.file_id
        file_name = message.audio.file_name or "аудио"
    elif message.document:
        file_id = message.document.file_id
        file_name = message.document.file_name or "документ"

    if file_id:
        print(f"\n Файл: {file_name}")
        print(f" Telegram file_id: {file_id}\n")
    else:
        print("Пожалуйста, отправьте именно файл или аудио.")

async def main():
    print("Бот-помощник запущен! Пересылайте или отправляйте файлы в чат, с которым связан бот.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
