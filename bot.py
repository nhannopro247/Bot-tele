import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import yt_dlp

# Lấy token bot từ biến môi trường
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Khởi tạo bot & dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Tạo menu phím bấm
menu_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📥 Tải video")],
        [KeyboardButton(text="📢 Thông báo"), KeyboardButton(text="ℹ️ Hướng dẫn")]
    ],
    resize_keyboard=True
)

# Lệnh /start
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("🤖 Xin chào! Chọn một chức năng:", reply_markup=menu_keyboard)

# Xử lý nút bấm "📥 Tải video"
@dp.message(lambda message: message.text == "📥 Tải video")
async def download_video(message: types.Message):
    await message.answer("🎥 Gửi link video YouTube hoặc TikTok để tải:")

# Nhận link và tải video
@dp.message(lambda message: message.text.startswith("http"))
async def process_video_link(message: types.Message):
    url = message.text
    await message.answer("⏳ Đang tải video, vui lòng chờ...")

    # Cấu hình yt-dlp
    ydl_opts = {
        "format": "bestvideo+bestaudio/best",
        "outtmpl": "video.mp4"
    }

    # Tải video
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        with open("video.mp4", "rb") as video:
            await bot.send_video(message.chat.id, video)
        os.remove("video.mp4")  # Xóa file sau khi gửi
    except Exception as e:
        await message.answer(f"❌ Lỗi: {str(e)}")

# Xử lý nút bấm "📢 Thông báo"
@dp.message(lambda message: message.text == "📢 Thông báo")
async def send_notification(message: types.Message):
    await message.answer("🔔 Nhập tin nhắn bạn muốn gửi tới tất cả người dùng:")

# Gửi tin nhắn đến tất cả user (giả sử bạn có danh sách ID user)
USER_IDS = []  # Cần thay danh sách này bằng ID thật
@dp.message(lambda message: message.text and message.reply_to_message and message.reply_to_message.text == "🔔 Nhập tin nhắn bạn muốn gửi tới tất cả người dùng:")
async def broadcast(message: types.Message):
    for user_id in USER_IDS:
        try:
            await bot.send_message(user_id, f"📢 Thông báo: {message.text}")
        except:
            pass
    await message.answer("✅ Đã gửi thông báo!")

# Xử lý nút bấm "ℹ️ Hướng dẫn"
@dp.message(lambda message: message.text == "ℹ️ Hướng dẫn")
async def guide(message: types.Message):
    await message.answer("📝 Hướng dẫn sử dụng bot:\n1️⃣ Bấm '📥 Tải video' để gửi link YouTube/TikTok.\n2️⃣ Bấm '📢 Thông báo' để gửi tin nhắn hàng loạt.\n3️⃣ Luôn nhập lệnh hợp lệ để tránh lỗi!")

# Mọi tin nhắn khác sẽ hiển thị lại menu
@dp.message()
async def fallback(message: types.Message):
    await message.answer("⚡ Vui lòng chọn một chức năng:", reply_markup=menu_keyboard)

# Chạy bot
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
