import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# ================== SOZLAMALAR ==================
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("BOT_TOKEN not set")

CHANNEL_USERNAME = "@bir_iqtibos"

# ================== MATNLAR ==================
MAIN_TEXT = (
    "Assalomu alaykum! 👋\n\n"
    "Siz @bir_iqtibos kanalining rasmiy botidasiz 🤖\n\n"
    "Bu yerda:\n"
    "🔹 Iqtibos va she’rlarni izlash\n"
    "🔹 Tanlov va challangelarda qatnashish\n"
    "🔹 Taklif va talab yuborish mumkin\n\n"
    "Quyidagi tugmalardan birini tanlang 👇"
)

SEARCH_TEXT = (
    "🔍 Iqtibos yoki she’rni topish uchun\n"
    "esingizda qolgan 1–2 ta so‘zni yozing.\n\n"
    "Masalan:\n"
    "• sog‘inch\n"
    "• yurak"
)

NO_CHALLENGE_TEXT = (
    "🏆 Hozirda faol tanlov yoki challenge yo‘q.\n\n"
    "📢 Yangi tanlovlar @bir_iqtibos kanalida e’lon qilinadi."
)

FEEDBACK_TEXT = (
    "✍️ Taklif yoki talabingizni yozing.\n"
    "Biz uni albatta ko‘rib chiqamiz."
)

# ================== TUGMALAR ==================
def main_menu():
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🔍 Iqtiboslarni izlash", callback_data="search")],
            [InlineKeyboardButton("🏆 Qatnashish", callback_data="join")],
            [InlineKeyboardButton("✍️ Taklif yoki talab yuborish", callback_data="feedback")],
        ]
    )

def back_menu():
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("⬅️ Orqaga qaytish", callback_data="back")]]
    )

# ================== XAVFSIZ EDIT ==================
async def safe_edit(query, text, keyboard):
    try:
        await query.edit_message_text(text=text, reply_markup=keyboard)
    except Exception:
        pass  # Message is not modified xatosini yutib yuboramiz

# ================== HANDLERLAR ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        text=MAIN_TEXT,
        reply_markup=main_menu()
    )

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "search":
        await safe_edit(query, SEARCH_TEXT, back_menu())

    elif query.data == "join":
        await safe_edit(query, NO_CHALLENGE_TEXT, back_menu())

    elif query.data == "feedback":
        await safe_edit(query, FEEDBACK_TEXT, back_menu())

    elif query.data == "back":
        await safe_edit(query, MAIN_TEXT, main_menu())

# ================== ISHGA TUSHISH ==================
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))

    print("Bot ishga tushdi...")
    app.run_polling()
