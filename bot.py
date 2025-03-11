import os
import asyncio
import yt_dlp
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.executor import start_polling

# Lấy BOT_TOKEN từ biến môi trường (Railway)
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")  # ID Admin để nhận thông báo lỗi

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# Kết nối SQLite để lưu lịch sử tải video
conn = sqlite3.connect("history.db")
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS history (user_id INTEGER, video_url TEXT)")
conn.commit()

# Giao diện nút bấm chính
main_menu = ReplyKeyboardMarkup(resize_keyboard=True)
main_menu.add(KeyboardButton("🎥 Tải Video"), KeyboardButton("📜 Lịch Sử"))

# Khi người dùng bắt đầu hoặc hoàn thành tác vụ
async def show_main_menu(chat_id):
    await bot.send_message(chat_id, "🔍 Chọn tác vụ:", reply_markup=main_menu)

# Khi người dùng bắt đầu
@dp.message_handler(commands=["start"])
async def send_welcome(message: Message):
    await message.answer("👋 Chào bạn! Gửi link video để tải xuống.", reply_markup=main_menu)

# Khi người dùng bấm "Tải Video"
@dp.message_handler(lambda message: message.text == "🎥 Tải Video")
async def ask_for_link(message: Message):
    await message.answer("📥 Gửi link video mà bạn muốn tải.")

# Khi người dùng bấm "Lịch Sử"
@dp.message_handler(lambda message: message.text == "📜 Lịch Sử")
async def show_history(message: Message):
    cursor.execute("SELECT video_url FROM history WHERE user_id=?", (message.from_user.id,))
    history = cursor.fetchall()
    
    if history:
        history_text = "\n".join([f"🔗 {link[0]}" for link in history[-5:]])  # Hiển thị 5 link gần nhất
        await message.answer(f"📜 Lịch sử tải:\n{history_text}")
    else:
        await message.answer("❌ Bạn chưa tải video nào.")

    await show_main_menu(message.chat.id)  # Quay lại menu chính

# Khi nhận link video
@dp.message_handler(lambda message: "http" in message.text)
async def download_video(message: Message):
    url = message.text
    msg = await message.reply("⏳ Đang xử lý...")

    # Giao diện chọn chất lượng video
    quality_keyboard = InlineKeyboardMarkup(row_width=2)
    quality_keyboard.add(
        InlineKeyboardButton("🔹 720p", callback_data=f"download|{url}|720p"),
        InlineKeyboardButton("🔸 480p", callback_data=f"download|{url}|480p"),
        InlineKeyboardButton("🎵 Âm thanh", callback_data=f"download|{url}|audio")
    )
    
    await msg.edit_text("🔽 Chọn chất lượng video:", reply_markup=quality_keyboard)

# Xử lý khi chọn chất lượng video
@dp.callback_query_handler(lambda call: call.data.startswith("download"))
async def process_download(call):
    _, url, quality = call.data.split("|")
    msg = await call.message.edit_text("⏳ Đang tải video...")

    ydl_opts = {
        "format": "bestvideo[height<=720]+bestaudio/best" if quality == "720p" else
                  "bestvideo[height<=480]+bestaudio/best" if quality == "480p" else
                  "bestaudio/best",
        "outtmpl": "video.mp4",
        "noplaylist": True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        file_size = os.path.getsize("video.mp4") / (1024 * 1024)  # MB
        if file_size > 50:  # Telegram giới hạn 50MB
            await call.message.edit_text(f"📂 File quá lớn ({file_size:.2f} MB), tải tại: {url}")
        else:
            with open("video.mp4", "rb") as video:
                await bot.send_video(call.message.chat.id, video)
        
        os.remove("video.mp4")  # Xóa video sau khi gửi
        cursor.execute("INSERT INTO history (user_id, video_url) VALUES (?, ?)", (call.from_user.id, url))
        conn.commit()

        await msg.delete()  # Xóa tin nhắn xử lý

    except Exception as e:
        await bot.send_message(ADMIN_ID, f"🚨 Lỗi bot: {e}")
        await call.message.edit_text("❌ Không thể tải video.")

    await show_main_menu(call.message.chat.id)  # Quay lại menu chính

# Chế độ admin - Gửi thông báo đến tất cả người dùng
@dp.message_handler(commands=["broadcast"])
async def broadcast_message(message: Message):
    if str(message.from_user.id) == ADMIN_ID:
        text = message.text.replace("/broadcast ", "")
        confirm_keyboard = InlineKeyboardMarkup()
        confirm_keyboard.add(
            InlineKeyboardButton("✅ Xác nhận", callback_data=f"confirm_broadcast|{text}"),
            InlineKeyboardButton("❌ Hủy", callback_data="cancel_broadcast")
        )
        await message.answer("📢 Bạn có chắc chắn muốn gửi thông báo này?", reply_markup=confirm_keyboard)
    else:
        await message.answer("❌ Bạn không có quyền sử dụng lệnh này.")

@dp.callback_query_handler(lambda call: call.data.startswith("confirm_broadcast"))
async def confirm_broadcast(call):
    _, text = call.data.split("|")
    cursor.execute("SELECT DISTINCT user_id FROM history")
    users = cursor.fetchall()
    
    for user in users:
        try:
            await bot.send_message(user[0], f"📢 Thông báo từ Admin:\n{text}")
        except:
            pass
    
    await call.message.edit_text("✅ Đã gửi thông báo đến tất cả người dùng.")

@dp.callback_query_handler(lambda call: call.data == "cancel_broadcast")
async def cancel_broadcast(call):
    await call.message.edit_text("❌ Hủy gửi thông báo.")

# Khi người dùng gửi tin nhắn không hợp lệ
@dp.message_handler(lambda message: message.text not in ["🎥 Tải Video", "📜 Lịch Sử"])
async def invalid_message(message: Message):
    await message.answer("⚠️ Vui lòng chọn một tác vụ trước.", reply_markup=main_menu)

# Chạy bot
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(bot.send_message(ADMIN_ID, "✅ Bot đã khởi động!"))
    start_polling(dp, skip_updates=True)
