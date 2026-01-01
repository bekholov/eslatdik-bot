import os, json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

# ================== SOZLAMALAR ==================
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("BOT_TOKEN not set")

ADMIN_IDS = {6520710677}            # <-- ADMIN USER ID
ADMIN_GROUP_ID = -1003566340125     # <-- ADMIN GROUP ID
CHANNEL_USERNAME = "@bir_iqtibos"

POSTS_FILE = "posts.json"
CONFIG_FILE = "config.json"
USERS_FILE = "users.json"

# ================== FILE YORDAMCHI ==================
def load_json(file, default):
    if not os.path.exists(file):
        with open(file, "w", encoding="utf-8") as f:
            json.dump(default, f)
    with open(file, encoding="utf-8") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ================== MA'LUMOTLAR ==================
posts = load_json(POSTS_FILE, [])
config = load_json(CONFIG_FILE, {"challenge": False})
users = load_json(USERS_FILE, [])

# ================== MATNLAR ==================
MAIN_TEXT = (
    "Assalomu alaykum! 👋\n\n"
    "Bu @bir_iqtibos kanalining rasmiy botidir 🤖\n\n"
    "🔍 Iqtibos va she’rlarni izlash\n"
    "🏆 Tanlov va challangelarda qatnashish\n"
    "✍️ Taklif va talab yuborish\n\n"
    "Kerakli bo‘limni tanlang 👇"
)

SEARCH_TEXT = "🔍 Qidirish uchun 1–2 ta so‘z yozing."
NO_CHALLENGE = "❌ Hozir faol challenge yo‘q."
FEEDBACK_TEXT = "✍️ Taklif yoki talabingizni yozing."

# ================== TUGMALAR ==================
def user_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔍 Qidiruv", callback_data="search")],
        [InlineKeyboardButton("🏆 Qatnashish", callback_data="join")],
        [InlineKeyboardButton("✍️ Taklif yuborish", callback_data="feedback")]
    ])

def admin_menu():
    status = "🟢 ON" if config["challenge"] else "🔴 OFF"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🏆 Challenge {status}", callback_data="toggle")],
        [InlineKeyboardButton("➕ Post qo‘shish", callback_data="add_post")],
        [InlineKeyboardButton("📊 Statistika", callback_data="stats")]
    ])

def back_btn():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Orqaga", callback_data="back")]
    ])

# ================== XAVFSIZ EDIT ==================
async def safe_edit(q, text, kb):
    try:
        await q.edit_message_text(text, reply_markup=kb)
    except:
        pass

# ================== START ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in users:
        users.append(uid)
        save_json(USERS_FILE, users)

    await update.message.reply_text(MAIN_TEXT, reply_markup=user_menu())

    if uid in ADMIN_IDS:
        await update.message.reply_text("👑 Admin panel:", reply_markup=admin_menu())

# ================== BUTTONS ==================
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id

    if q.data == "search":
        context.user_data["mode"] = "search"
        await safe_edit(q, SEARCH_TEXT, back_btn())

    elif q.data == "join":
        text = "📝 Ro‘yxatdan o‘ting" if config["challenge"] else NO_CHALLENGE
        await safe_edit(q, text, back_btn())

    elif q.data == "feedback":
        context.user_data["mode"] = "feedback"
        await safe_edit(q, FEEDBACK_TEXT, back_btn())

    elif q.data == "back":
        context.user_data.clear()
        await safe_edit(q, MAIN_TEXT, user_menu())

    # ===== ADMIN ONLY =====
    elif uid in ADMIN_IDS:
        if q.data == "toggle":
            config["challenge"] = not config["challenge"]
            save_json(CONFIG_FILE, config)
            await safe_edit(q, "Holat o‘zgartirildi", admin_menu())

        elif q.data == "add_post":
            context.user_data["mode"] = "add_post"
            await safe_edit(q, "Post matnini yuboring:", back_btn())

        elif q.data == "stats":
            await safe_edit(
                q,
                f"👥 Userlar: {len(users)}\n📚 Postlar: {len(posts)}",
                admin_menu()
            )

# ================== TEXT ==================
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    mode = context.user_data.get("mode")

    if mode == "search":
        key = update.message.text.lower()
        results = [p for p in posts if key in p["text"].lower()]
        if not results:
            await update.message.reply_text("❌ Hech narsa topilmadi.", reply_markup=user_menu())
        else:
            msg = "🔍 Natijalar:\n\n"
            for p in results[:5]:
                msg += f"{p['text']}\n🔗 {p['link']}\n\n"
            await update.message.reply_text(msg, reply_markup=user_menu())
        context.user_data.clear()

    elif mode == "feedback":
        user = update.effective_user
        await context.bot.send_message(
            ADMIN_GROUP_ID,
            f"📩 Feedback\n👤 {user.full_name}\n🆔 {user.id}\n\n{update.message.text}"
        )
        context.user_data.clear()
        await update.message.reply_text("✅ Yuborildi", reply_markup=user_menu())

    elif mode == "add_post" and uid in ADMIN_IDS:
        text = update.message.text
        link = f"https://t.me/{CHANNEL_USERNAME.strip('@')}/{len(posts)+1}"
        posts.append({"text": text, "link": link})
        save_json(POSTS_FILE, posts)
        context.user_data.clear()
        await update.message.reply_text("✅ Post saqlandi", reply_markup=admin_menu())

# ================== ADMIN REPLY ==================
async def reply_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    if len(context.args) < 2:
        await update.message.reply_text("Format: /reply USER_ID matn")
        return
    uid = int(context.args[0])
    text = " ".join(context.args[1:])
    await context.bot.send_message(uid, f"📩 Admin javobi:\n\n{text}")
    await update.message.reply_text("✅ Yuborildi")

# ================== RUN ==================
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reply", reply_cmd))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    print("Bot ishga tushdi...")
    app.run_polling()
