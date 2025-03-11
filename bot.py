import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import yt_dlp
from fastapi import FastAPI
import uvicorn

# Lấy token bot & admin ID từ biến môi trường
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))  # ID admin (mặc định 0 nếu chưa có)

# Khởi tạo bot & dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Tạo Web Server giả để Render không báo lỗi cổng
app = FastAPI()

@app.get("/")
def home():
    return {"status": "Bot is running!"}

# Giao diện nút bấm
menu_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📥 Tải video")],
        [KeyboardButton(text="📢 Gửi thông báo"), KeyboardButton(text="ℹ️ Hướng dẫn")]
    ],
    resize_keyboard=True
)

# Lệnh /start
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("🤖 Xin chào! Chọn một chức năng:", reply_markup=menu_keyboard)
    if message.from_user.id == ADMIN_ID:
        await message.answer("🔧 Bạn đang đăng nhập với quyền Admin!")

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

# Xử lý nút bấm "📢 Gửi thông báo" (chỉ Admin mới thấy)
@dp.message(lambda message: message.text == "📢 Gửi thông báo")
async def admin_broadcast(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("✉️ Nhập nội dung thông báo để gửi đến tất cả user:")
    else:
        await message.answer("🚫 Bạn không có quyền sử dụng chức năng này!")

# Gửi tin nhắn đến tất cả user (giả sử có danh sách ID user)
USER_IDS = []  # Cần thay bằng danh sách ID user thật
@dp.message(lambda message: message.text and message.from_user.id == ADMIN_ID)
async def send_broadcast(message: types.Message):
    for user_id in USER_IDS:
        try:
            await bot.send_message(user_id, f"📢 Thông báo: {message.text}")
        except:
            pass
    await message.answer("✅ Đã gửi thông báo!")

# Xử lý nút bấm "ℹ️ Hướng dẫn"
@dp.message(lambda message: message.text == "ℹ️ Hướng dẫn")
async def guide(message: types.Message):
    await message.answer("📝 Hướng dẫn sử dụng bot:\n1️⃣ Bấm '📥 Tải video' để gửi link YouTube/TikTok.\n2️⃣ Admin có thể gửi thông báo đến user!")

# Mọi tin nhắn khác sẽ hiển thị lại menu
@dp.message()
async def fallback(message: types.Message):
    await message.answer("⚡ Vui lòng chọn một chức năng:", reply_markup=menu_keyboard)

# Chạy bot & FastAPI server đúng cách
async def start_bot():
    if ADMIN_ID:
        try:
            await bot.send_message(ADMIN_ID, "✅ Bot đã khởi động thành công!")
        except Exception as e:
            print(f"⚠️ Không thể gửi tin nhắn đến admin: {e}")
    await dp.start_polling(bot)

# Chạy bot trong event loop
def run():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(start_bot())  # Chạy bot
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))  # Chạy web server

if __name__ == "__main__":
    run()
