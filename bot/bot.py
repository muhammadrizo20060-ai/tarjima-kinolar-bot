import logging
import os
from threading import Thread
from flask import Flask
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

# --- KEEP-ALIVE WEB SERVER ---
app = Flask(__name__)


@app.route('/')
def home():
    return "Bot is running!"


def run_web():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8000)))


def keep_alive():
    t = Thread(target=run_web, daemon=True)
    t.start()

# --- SOZLAMALAR ---
API_TOKEN = os.environ['BOT_TOKEN']
ADMIN_ID = 5948284301  # Bu @mahmudovvx ning shaxsiy ID raqami

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# --- KINO BAZASI ---
# O'zingiz xohlagan kodlarni shu yerga qo'shib borasiz
movies = {
    "100": "BAACAgEAAxkBAAMVaetLZu51DnkuL-rCwMXToK2zrG4AAv4LAAIyYZlGUwRpc0DEBFc7BA",
}


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer(
        f"Assalomu alaykum, {message.from_user.first_name}!\n\n"
        "🎬 **@tarjima_kinolar13_bot** botiga xush kelibsiz.\n"
        "Kino ko'rish uchun uning kodini yozib yuboring.\n\n"
        "👤 Admin: @mahmudovvx"
    )


# ADMIN (Siz) VIDEO YUBORGANDA ID OLISH
@dp.message_handler(content_types=['video'])
async def get_id(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        vid_id = message.video.file_id
        await message.answer(
            f"✅ **Kino ID-si tayyor!**\n\n"
            f"Ushbu kodni nusxalab, Replit-dagi `movies` lug'atiga qo'shing:\n\n"
            f"`{vid_id}`",
            parse_mode="Markdown"
        )
    else:
        await message.answer("Iltimos, faqat kino kodini yuboring! 🎥")


# KOD ORQALI KINO QIDIRISH
@dp.message_handler()
async def check_code(message: types.Message):
    code = message.text
    if code in movies:
        await message.answer_video(
            video=movies[code],
            caption=f"✅ Kino kodi: {code}\n🍿 Yoqimli tomosha!\n\nBot: @tarjima_kinolar13_bot"
        )
    else:
        await message.answer("❌ Kechirasiz, bunday kodli kino hali bazada yo'q.")


if __name__ == '__main__':
    keep_alive()
    executor.start_polling(dp, skip_updates=True)
