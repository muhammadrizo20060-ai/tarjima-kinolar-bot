import logging
import os
import sqlite3
from threading import Thread, Lock
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
DB_PATH = os.path.join(os.path.dirname(__file__), 'movies.db')

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# --- DATABASE ---
db_lock = Lock()


def db_conn():
    return sqlite3.connect(DB_PATH)


def init_db():
    with db_lock, db_conn() as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS movies ("
            "code TEXT PRIMARY KEY, file_id TEXT NOT NULL)"
        )
        cur = conn.execute("SELECT COUNT(*) FROM movies")
        if cur.fetchone()[0] == 0:
            seed = {
                "1": "BAACAgQAAxkBAANAaet2sY5LSEy-9DlGTIC5o51JSyUAAqoQAAL64MlTtWhK3fzIdRU7BA",
                "2": "BAACAgQAAxkBAANCaet2t8_T4fj4YZhh-IWbQQ9Pqh8AAnEYAALNDqFQSXXFhcqD2ks7BA",
                "3": "BAACAgQAAxkBAANAaet2sY5LSEy-9DlGTIC5o51JSyUAAqoQAAL64MlTtWhK3fzIdRU7BA",
                "100": "BAACAgEAAxkBAAMVaetLZu51DnkuL-rCwMXToK2zrG4AAv4LAAIyYZlGUwRpc0DEBFc7BA",
                "101": "BAACAgIAAxkBAAM5aety54oze2DLgHHUbjCt1ZyNlrEAAtaCAALj2GFJQfQUnnOMvCo7BA",
            }
            conn.executemany(
                "INSERT INTO movies (code, file_id) VALUES (?, ?)",
                seed.items(),
            )


def get_movie(code: str):
    with db_lock, db_conn() as conn:
        cur = conn.execute(
            "SELECT file_id FROM movies WHERE code = ?", (code,)
        )
        row = cur.fetchone()
        return row[0] if row else None


def save_movie(code: str, file_id: str):
    with db_lock, db_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO movies (code, file_id) VALUES (?, ?)",
            (code, file_id),
        )


def delete_movie(code: str) -> bool:
    with db_lock, db_conn() as conn:
        cur = conn.execute("DELETE FROM movies WHERE code = ?", (code,))
        return cur.rowcount > 0


def list_movies():
    with db_lock, db_conn() as conn:
        cur = conn.execute("SELECT code FROM movies ORDER BY code")
        return [r[0] for r in cur.fetchall()]


# --- ADMIN PENDING STATE ---
# When admin sends a video, we remember its file_id and wait for the next
# message (the code) to save the pair to the database.
pending_video = {}  # admin_user_id -> file_id


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer(
        f"Assalomu alaykum, {message.from_user.first_name}!\n\n"
        "🎬 **@tarjima_kinolar13_bot** botiga xush kelibsiz.\n"
        "Kino ko'rish uchun uning kodini yozib yuboring.\n\n"
        "👤 Admin: @mahmudovvx"
    )


@dp.message_handler(commands=['list'])
async def list_codes(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    codes = list_movies()
    if not codes:
        await message.answer("Baza bo'sh.")
        return
    await message.answer(
        f"📚 Bazadagi kinolar ({len(codes)} ta):\n\n" + ", ".join(codes)
    )


@dp.message_handler(commands=['cancel'])
async def cancel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    if pending_video.pop(message.from_user.id, None):
        await message.answer("❎ Bekor qilindi.")
    else:
        await message.answer("Bekor qilinadigan video yo'q.")


@dp.message_handler(commands=['delete'])
async def delete_cmd(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        await message.answer("Foydalanish: `/delete KOD`", parse_mode="Markdown")
        return
    code = parts[1].strip()
    if delete_movie(code):
        await message.answer(f"🗑 Kod `{code}` o'chirildi.", parse_mode="Markdown")
    else:
        await message.answer(f"❌ Kod `{code}` topilmadi.", parse_mode="Markdown")


# ADMIN VIDEO YUBORGANDA — saqlash jarayonini boshlash
@dp.message_handler(content_types=['video'])
async def on_video(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("Iltimos, faqat kino kodini yuboring! 🎥")
        return
    pending_video[message.from_user.id] = message.video.file_id
    await message.answer(
        "✅ Video qabul qilindi.\n\n"
        "Endi shu kino uchun **kod** yuboring (masalan: `102`).\n"
        "Bekor qilish uchun /cancel yuboring.",
        parse_mode="Markdown"
    )


# KOD ORQALI KINO QIDIRISH (yoki admin saqlash bosqichi)
@dp.message_handler()
async def on_text(message: types.Message):
    code = (message.text or "").strip()

    # Admin saqlash bosqichi — agar oldin video yuborilgan bo'lsa
    if (
        message.from_user.id == ADMIN_ID
        and message.from_user.id in pending_video
    ):
        file_id = pending_video.pop(message.from_user.id)
        save_movie(code, file_id)
        await message.answer(
            f"✅ Saqlandi!\n\n"
            f"Kod: `{code}`\n"
            f"Foydalanuvchilar endi `{code}` yozib bu kinoni ko'ra oladi.",
            parse_mode="Markdown"
        )
        return

    file_id = get_movie(code)
    if file_id:
        await message.answer_video(
            video=file_id,
            caption=f"✅ Kino kodi: {code}\n🍿 Yoqimli tomosha!\n\nBot: @tarjima_kinolar13_bot"
        )
    else:
        await message.answer("❌ Kechirasiz, bunday kodli kino hali bazada yo'q.")


if __name__ == '__main__':
    init_db()
    keep_alive()
    executor.start_polling(dp, skip_updates=True)
