import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from fastapi import FastAPI
import uvicorn

# Bật logging để kiểm tra bot có nhận tin nhắn không
logging.basicConfig(level=logging.INFO)

# Lấy token bot từ biến môi trường
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Khởi tạo bot & dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Tạo Web Server giả để Render không báo lỗi cổng
app = FastAPI()

@app.get("/")
async def home():
    return {"status": "Bot is running!"}

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

# Chạy bot Telegram trong background
async def start_bot():
    while True:
        try:
            logging.info("✅ Bắt đầu chạy bot Telegram...")
            await dp.start_polling(bot)
        except Exception as e:
            logging.error(f"❌ Lỗi bot: {e}")
        await asyncio.sleep(5)  # Nếu bot bị lỗi, thử lại sau 5 giây

# Chạy bot & web server cùng lúc
def run():
    loop = asyncio.get_event_loop()
    loop.create_task(start_bot())  # Chạy bot Telegram song song
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))  # Chạy web server

if __name__ == "__main__":
    run()
