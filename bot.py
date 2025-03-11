import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import logging

# Bật logging để kiểm tra bot có nhận tin nhắn không
logging.basicConfig(level=logging.INFO)

# Lấy token bot từ biến môi trường
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Khởi tạo bot & dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Kiểm tra khi bot khởi động
async def on_startup():
    print("✅ Bot đã khởi động!")
    logging.info("✅ Bot đang chạy!")

# Lệnh /start
@dp.message(Command("start"))
async def start(message: types.Message):
    logging.info(f"📩 Nhận lệnh từ {message.from_user.id}: /start")
    await message.answer("🤖 Xin chào! Bot đã sẵn sàng!")

# Xử lý tin nhắn bất kỳ
@dp.message()
async def handle_message(message: types.Message):
    logging.info(f"📩 Nhận tin nhắn từ {message.from_user.id}: {message.text}")
    await message.answer("⚡ Bạn vừa gửi: " + message.text)

# Chạy bot
async def main():
    await on_startup()  # Kiểm tra bot đã khởi động chưa
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
