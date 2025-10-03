# bot.py
# Працює з python-telegram-bot (v20+)

import datetime
import random
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

BOT_TOKEN = "8305292946:AAFT5CseWNrriB9tKCK9mNl_BpZR1JwtlvU"  # ⚠️ заміни на свій

# ---- ЗБЕРІГАННЯ ----
users = {}  # user_id -> дані
clans = {}  # clan_name -> список user_id
referrals = {}  # user_id -> кто пригласил

# ---- ХЕЛПЕРИ ----
def ensure_user(user_id):
    if user_id not in users:
        users[user_id] = {
            "balance": 1000,
            "start_time": datetime.datetime.now(),
            "clan": None,
            "referrals": 0,
        }

def get_profile_text(user_id):
    user = users[user_id]
    balance = user["balance"]
    clan = user["clan"] if user["clan"] else "❌ Нет"
    diff = datetime.datetime.now() - user["start_time"]
    days, hours = diff.days, diff.seconds // 3600

    return (
        f"📊 Профиль игрока:\n"
        f"💵 Баланс: {balance}$\n"
        f"⌚ Время в игре: {days} дн. {hours} ч.\n"
        f"👨‍👩‍👦 Клан: {clan}\n"
    )

def get_main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎰 Казино", callback_data="casino"),
         InlineKeyboardButton("🎲 Кубик", callback_data="dice")],
        [InlineKeyboardButton("🎯 Дартс", callback_data="darts"),
         InlineKeyboardButton("🎳 Боулинг", callback_data="bowling")],
        [InlineKeyboardButton("🏀 Баскетбол", callback_data="basketball")],
        [InlineKeyboardButton("👨‍👩‍👦 Кланы", callback_data="clans"),
         InlineKeyboardButton("🏆 Топ-10", callback_data="top")],
    ])

# ---- /start ----
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ensure_user(user.id)

    # Реферальна система
    if context.args:
        inviter_id = int(context.args[0])
        if inviter_id != user.id and inviter_id in users and user.id not in referrals:
            users[inviter_id]["balance"] += 500
            users[inviter_id]["referrals"] += 1
            referrals[user.id] = inviter_id

    text = (
        f"👋 Привет, {user.first_name}!\n"
        f"Ты попал в игровой бот. Стартовый баланс: 1000$.\n\n"
        f"Используй кнопки ниже:"
    )
    await update.message.reply_text(text, reply_markup=get_main_menu())

# ---- ИГРЫ ----
async def play_game(user_id, game, win_amount, lose_amount, win_chance=0.5):
    user = users[user_id]
    if random.random() < win_chance:
        user["balance"] += win_amount
        return f"{game}: Победа! +{win_amount}$"
    else:
        user["balance"] -= lose_amount
        return f"{game}: Проигрыш! -{lose_amount}$"

# ---- CALLBACKS ----
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    ensure_user(user_id)

    if query.data == "casino":
        text = await play_game(user_id, "🎰 Казино", 100, 100)
    elif query.data == "dice":
        text = await play_game(user_id, "🎲 Кубик", 50, 50, win_chance=0.5)
    elif query.data == "darts":
        text = await play_game(user_id, "🎯 Дартс", 100, 30, win_chance=0.2)
    elif query.data == "bowling":
        text = await play_game(user_id, "🎳 Боулинг", 80, 20, win_chance=0.25)
    elif query.data == "basketball":
        text = await play_game(user_id, "🏀 Баскетбол", 70, 25, win_chance=0.4)
    elif query.data == "clans":
        return await show_clans(query, context)
    elif query.data.startswith("join_"):
        return await join_clan(query, query.data.split("_", 1)[1])
    elif query.data == "top":
        return await show_top(query)

    else:
        text = "❓ Неизвестная команда"

    await query.edit_message_text(
        text=get_profile_text(user_id) + "\n" + text,
        reply_markup=get_main_menu()
    )

# ---- КЛАНЫ ----
async def show_clans(query, context):
    if clans:
        buttons = [[InlineKeyboardButton(f"{name} ({len(members)})", callback_data=f"join_{name}")]
                   for name, members in clans.items()]
    else:
        buttons = [[InlineKeyboardButton("Создать клан (вступишь сам)", callback_data="join_NewClan")]]
    buttons.append([InlineKeyboardButton("⬅️ Назад", callback_data="back")])
    await query.edit_message_text("👨‍👩‍👦 Доступные кланы:", reply_markup=InlineKeyboardMarkup(buttons))

async def join_clan(query, clan_name):
    user_id = query.from_user.id
    ensure_user(user_id)

    if clan_name not in clans:
        clans[clan_name] = []
    clans[clan_name].append(user_id)
    users[user_id]["clan"] = clan_name

    await query.edit_message_text(
        f"✅ Ты вступил в клан: {clan_name}",
        reply_markup=get_main_menu()
    )

# ---- ТОП ----
async def show_top(query):
    ranking = sorted(users.items(), key=lambda x: x[1]["balance"], reverse=True)[:10]
    text = "🏆 ТОП-10 игроков по балансу:\n"
    for i, (uid, data) in enumerate(ranking, start=1):
        text += f"{i}. {data.get('name', str(uid))} — {data['balance']}$\n"

    await query.edit_message_text(text, reply_markup=get_main_menu())

# ---- MAIN ----
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Bot started...")
    app.run_polling()

if __name__ == "__main__":
    main()
