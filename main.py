import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Kinolar bazasi - Siz yuborgan yangi ID bilan
movies = {
    "100": "BAACAgEAAxkBAAMVaetLZu51DnkuL-rCwMXToK2zrG4AAv4LAAIyYZlGUwRpc0DEBFc7BA",
    "3": "BAACAgIAAxkBAAM9aet2bV9oT5unRHk3KDohDAABl-xhAAIGgwACLfChSzI6-b2gd2p8OwQ",
    "1": "BAACAgQAAxkBAANAaet2sY5LSEy-9DlGTIC5o51JSyUAAqoQAAL64MlTtWhK3fzIdRU7BA",
    "2": "BAACAgQAAxkBAANCaet2t8_T4fj4YZhh-IWbQQ9Pqh8AAnEYAALNDqFQSXXFhcqD2ks7BA",
    "101": "BAACAgIAAxkBAAM5aety54oze2DLgHHubjCt1ZyNlrEAAtacaALj2GFJQfQUnnOMvCo7BA"
}
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Assalomu alaykum! Kino kodini yuboring.")

async def get_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text
    if code in movies:
        await update.message.reply_video(video=movies[code], caption=f"Kino kodi: {code}")
    else:
        await update.message.reply_text("Xato kod! Bunday kino topilmadi.")

if __name__ == '__main__':
    token = os.environ.get("BOT_TOKEN")
    if not token:
        print("XATO: BOT_TOKEN topilmadi!")
    else:
        app = ApplicationBuilder().token(token).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), get_movie))
        print("Bot ishga tushdi...")
        app.run_polling()
