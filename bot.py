import csv
import os
import asyncio
from datetime import datetime
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ================== SOZLAMALAR ==================
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN not set")

CHANNEL_USERNAME = "@bir_iqtibos"
ADMIN_ID = 6520710677
ADMIN_GROUP_ID = -1003566340125

STATE_FILE = "challenge_state.txt"
CSV_FILE = "participants.csv"

VILOYATLAR = [
    "Toshkent", "Andijon", "Farg‘ona", "Namangan",
    "Samarqand", "Buxoro", "Xorazm", "Qashqadaryo",
    "Surxondaryo", "Jizzax", "Sirdaryo", "Navoiy"
]

# ================== XOTIRA ==================
main_message_id = {}   # user_id -> message_id
user_mode = {}         # search / feedback / join
user_steps = {}
temp_data = {}

# ================== CHALLENGE ==================
def get_challenge_state():
    if not os.path.exists(STATE_FILE):
        return False
    with open(STATE_FILE) as f:
        return f.read().strip() == "ON"

def set_challenge_state(state: bool):
    with open(STATE_FILE, "w") as f:
        f.write("ON" if state else "OFF")

# ================== CSV ==================
def init_csv():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "№", "Ism familiya", "Username",
                "Viloyat", "Tuman/Shahar", "Sana"
            ])

def get_next_number():
    with open(CSV_FILE, encoding="utf-8") as f:
        return sum(1 for _ in f)

def already_registered(username):
    if not os.path.exists(CSV_FILE):
        return False
    with open(CSV_FILE, encoding="utf-8") as f:
        return username in f.read()

def save_user(data):
    number = get_next_number()
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            number,
            data["name"],
            data["username"],
            data["viloyat"],
            data["tuman"],
            data["time"]
        ])
    return number

# ================== MENYULAR ==================
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔍 Iqtiboslarni izlash", callback_data="search")],
        [InlineKeyboardButton("🏆 Qatnashish", callback_data="join")],
        [InlineKeyboardButton("📝 Taklif yoki talab yuborish", callback_data="feedback")]
    ])

def back_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Ortga qaytish", callback_data="back")]
    ])

# ================== ASOSIY MENYU ==================
async def render_main_menu(context, chat_id, user_id):
    active = get_challenge_state()
    status = "🟢 Ochiq" if active else "🔴 Yopiq"

    text = (
        "Assalomu alaykum! 👋\n\n"
        "Siz @bir_iqtibos kanalining rasmiy botidasiz 🤖\n\n"
        "📚 Kanalimizda she’rlar, iqtiboslar va aforizmlar joylanadi.\n\n"
        "🤖 Ushbu bot orqali siz:\n"
        "• iqtibos va she’rlarni qidirishingiz 🔍\n"
        "• tanlovlarda qatnashishingiz 🏆\n"
        "• taklif va talab yuborishingiz 📝\n"
        "mumkin.\n\n"
        f"🏆 Challenge holati: {status}\n\n"
        "Quyidagi tugmalardan birini tanlang 👇"
    )

    if user_id in main_message_id:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=main_message_id[user_id],
            text=text,
            reply_markup=main_menu()
        )
    else:
        msg = await context.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=main_menu()
        )
        main_message_id[user_id] = msg.message_id

# ================== START ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await render_main_menu(
        context,
        update.effective_chat.id,
        update.effective_user.id
    )

# ================== TUGMALAR ==================
async def search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_mode[query.from_user.id] = "search"

    await context.bot.edit_message_text(
        chat_id=query.message.chat_id,
        message_id=main_message_id[query.from_user.id],
        text=(
            "🔍 Izlash uchun esingizda qolgan\n"
            "1–2 ta so‘zni yozing.\n\n"
            "Masalan:\n"
            "• sog‘inch\n"
            "• yurak tun"
        ),
        reply_markup=back_menu()
    )

async def feedback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_mode[query.from_user.id] = "feedback"

    await context.bot.edit_message_text(
        chat_id=query.message.chat_id,
        message_id=main_message_id[query.from_user.id],
        text="✍️ Taklif yoki talabingizni yozing.\nBiz uni albatta ko‘rib chiqamiz.",
        reply_markup=back_menu()
    )

async def join_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not get_challenge_state():
        await context.bot.edit_message_text(
            chat_id=query.message.chat_id,
            message_id=main_message_id[query.from_user.id],
            text=(
                "⛔ Hozirda faol tanlov yoki challenge yo‘q.\n\n"
                "📢 Yangi tanlovlar @bir_iqtibos kanalida e’lon qilinadi."
            ),
            reply_markup=back_menu()
        )
        return

    init_csv()
    user = query.from_user
    if already_registered(user.username or str(user.id)):
        await context.bot.edit_message_text(
            chat_id=query.message.chat_id,
            message_id=main_message_id[user.id],
            text="ℹ️ Siz allaqachon ro‘yxatdan o‘tgansiz.",
            reply_markup=back_menu()
        )
        return

    user_steps[user.id] = "name"
    user_mode[user.id] = "join"

    await context.bot.edit_message_text(
        chat_id=query.message.chat_id,
        message_id=main_message_id[user.id],
        text="👤 Ismingiz va familiyangizni kiriting:",
        reply_markup=back_menu()
    )

async def back_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_mode.pop(query.from_user.id, None)
    user_steps.pop(query.from_user.id, None)
    temp_data.pop(query.from_user.id, None)
    await render_main_menu(context, query.message.chat_id, query.from_user.id)

# ================== TEXT ==================
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if user_mode.get(user_id) == "feedback":
        msg = (
            "📝 Yangi taklif / talab\n\n"
            f"👤 {update.effective_user.full_name}\n"
            f"@{update.effective_user.username or 'yo‘q'}\n\n"
            f"{text}"
        )
        await context.bot.send_message(ADMIN_GROUP_ID, msg)
        await render_main_menu(context, update.effective_chat.id, user_id)
        return

    if user_steps.get(user_id) == "name":
        temp_data[user_id] = {
            "name": text,
            "username": update.effective_user.username or ""
        }
        keyboard = [[InlineKeyboardButton(v, callback_data=v)] for v in VILOYATLAR]
        user_steps[user_id] = "viloyat"

        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=main_message_id[user_id],
            text="📍 Viloyatingizni tanlang:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    if user_steps.get(user_id) == "tuman":
        temp_data[user_id]["tuman"] = text
        temp_data[user_id]["time"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        save_user(temp_data[user_id])
        await render_main_menu(context, update.effective_chat.id, user_id)

async def viloyat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if user_steps.get(user_id) == "viloyat":
        temp_data[user_id]["viloyat"] = query.data
        user_steps[user_id] = "tuman"

        await context.bot.edit_message_text(
            chat_id=query.message.chat_id,
            message_id=main_message_id[user_id],
            text="🏙 Shahar yoki tumaningizni yozing:",
            reply_markup=back_menu()
        )

# ================== RUN ==================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(search_handler, pattern="search"))
app.add_handler(CallbackQueryHandler(join_handler, pattern="join"))
app.add_handler(CallbackQueryHandler(feedback_handler, pattern="feedback"))
app.add_handler(CallbackQueryHandler(back_handler, pattern="back"))
app.add_handler(CallbackQueryHandler(viloyat_handler))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

print("Bot ishga tushdi...")
app.run_polling()

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # BU YERDA SENING BOR HANDLERLARING QOLADI
    # masalan:
    # app.add_handler(CommandHandler("start", start))
    # app.add_handler(CallbackQueryHandler(button_handler))

    print("Bot ishga tushdi...")
    app.run_polling()

if __name__ == "__main__":
    main()
