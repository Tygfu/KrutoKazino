import asyncio
import os
import random
import time
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = "8305292946:AAFT5CseWNrriB9tKCK9mNl_BpZR1JwtlvU"
ADMIN_USERNAME = 6663798088  # Власник промокодів

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

USERS_DIR = "users"
CLANS_DIR = "clans"
MARKET_FILE = "market.txt"
PROMO_FILE = "promos.txt"

for directory in [USERS_DIR, CLANS_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

# Понерфлені значення для одиночних символів (в 2 рази)
SYMBOL_VALUES = {
    "BAR": 5,        # Було 10
    "SLIVKA": 10,    # Було 20
    "LEMON": 25,     # Було 50
    "SEVEN": 50      # Було 100
}

BUSINESSES = {
    "автомойка": (5000, 50),
    "ресторан": (25000, 300),
    "завод": (100000, 1500),
    "вышка": (1000000, 10000)
}

# По 2 варіанти на кожну рідкість титулів
TITLES_DB = {
    "Новичок": {"rarity": "Обычный", "reward_type": "money", "val": 500, "desc": "+500$ при получении"},
    "Работяга": {"rarity": "Обычный", "reward_type": "money", "val": 1000, "desc": "+1,000$ при получении"},
    "Счастливчик": {"rarity": "Редкий", "reward_type": "money", "val": 5000, "desc": "+5,000$ при получении"},
    "Капиталист": {"rarity": "Редкий", "reward_type": "money", "val": 15000, "desc": "+15,000$ при получении"},
    "Магнат": {"rarity": "Эпический", "reward_type": "biz", "val": "автомойка", "desc": "Дает бизнес Автомойка"},
    "Олигарх": {"rarity": "Эпический", "reward_type": "money", "val": 100000, "desc": "+100,000$ при получении"},
    "Тайкун": {"rarity": "Легендарный", "reward_type": "biz", "val": "ресторан", "desc": "Дает бизнес Ресторан"},
    "Владыка": {"rarity": "Легендарный", "reward_type": "money", "val": 500000, "desc": "+500,000$ при получении"},
    "Теневой Барон": {"rarity": "Мифический", "reward_type": "biz", "val": "вышка", "desc": "Дает бизнес Вышка!"},
    "Бог Богатства": {"rarity": "Мифический", "reward_type": "money", "val": 1000000, "desc": "+1,000,000$ при получении"}
}

# Спеціальні системні титули (не випадають, мін ціна від 10кк)
SYSTEM_TITLES = {
    "👑 Император": {"price": 10000000, "desc": "Эксклюзивный титул от игры"},
    "🌌 Абсолют": {"price": 50000000, "desc": "Высший статус в игре"}
}

RED_NUMBERS = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]

# Лобі рулетки: chat_id -> data
roulette_lobbies = {}

def load_user_data(user_id: int) -> dict:
    filepath = os.path.join(USERS_DIR, f"{user_id}.txt")
    data = {
        "balance": 1000.0,
        "bank": 0.0,
        "name": "Игрок",
        "referrer": "",
        "ref_count": 0,
        "last_bonus": 0,
        "last_work": 0,
        "last_rob": 0,
        "clan": "",
        "businesses": {},
        "titles": [],
        "used_promos": []
    }
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split("=")
                if len(parts) == 2:
                    key, val = parts[0], parts[1]
                    if key == "balance": data["balance"] = float(val)
                    elif key == "bank": data["bank"] = float(val)
                    elif key == "name": data["name"] = val
                    elif key == "referrer": data["referrer"] = val
                    elif key == "ref_count": data["ref_count"] = int(val)
                    elif key == "last_bonus": data["last_bonus"] = float(val)
                    elif key == "last_work": data["last_work"] = float(val)
                    elif key == "last_rob": data["last_rob"] = float(val)
                    elif key == "clan": data["clan"] = val
                    elif key == "titles": data["titles"] = [t for t in val.split(",") if t]
                    elif key == "used_promos": data["used_promos"] = [p for p in val.split(",") if p]
                    elif key.startswith("biz_"):
                        biz_name = key.replace("biz_", "")
                        data["businesses"][biz_name] = int(val)
    else:
        save_user_data(user_id, data)
    return data

def save_user_data(user_id: int, data: dict):
    filepath = os.path.join(USERS_DIR, f"{user_id}.txt")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"name={data['name']}\n")
        f.write(f"balance={data['balance']}\n")
        f.write(f"bank={data['bank']}\n")
        f.write(f"referrer={data['referrer']}\n")
        f.write(f"ref_count={data['ref_count']}\n")
        f.write(f"last_bonus={data['last_bonus']}\n")
        f.write(f"last_work={data['last_work']}\n")
        f.write(f"last_rob={data['last_rob']}\n")
        f.write(f"clan={data['clan']}\n")
        f.write(f"titles={','.join(data['titles'])}\n")
        f.write(f"used_promos={','.join(data['used_promos'])}\n")
        for biz, count in data["businesses"].items():
            f.write(f"biz_{biz}={count}\n")

def load_promos() -> dict:
    promos = {}
    if os.path.exists(PROMO_FILE):
        with open(PROMO_FILE, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split(":")
                if len(parts) == 3:
                    code, money, uses = parts[0], float(parts[1]), int(parts[2])
                    promos[code] = {"money": money, "uses": uses}
    return promos

def save_promos(promos: dict):
    with open(PROMO_FILE, "w", encoding="utf-8") as f:
        for code, data in promos.items():
            f.write(f"{code}:{data['money']}:{data['uses']}\n")

def load_market() -> list:
    items = []
    if os.path.exists(MARKET_FILE):
        with open(MARKET_FILE, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split(":")
                if len(parts) == 4:
                    items.append({
                        "id": int(parts[0]),
                        "seller_id": int(parts[1]),
                        "title": parts[2],
                        "price": float(parts[3])
                    })
    return items

def save_market(items: list):
    with open(MARKET_FILE, "w", encoding="utf-8") as f:
        for item in items:
            f.write(f"{item['id']}:{item['seller_id']}:{item['title']}:{item['price']}\n")

def load_clan_data(clan_name: str) -> dict:
    filepath = os.path.join(CLANS_DIR, f"{clan_name.lower()}.txt")
    if os.path.exists(filepath):
        data = {"name": clan_name, "owner": 0, "bank": 0.0, "members": []}
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split("=")
                if len(parts) == 2:
                    k, v = parts[0], parts[1]
                    if k == "name": data["name"] = v
                    elif k == "owner": data["owner"] = int(v)
                    elif k == "bank": data["bank"] = float(v)
                    elif k == "members": data["members"] = [int(x) for x in v.split(",") if x]
        return data
    return None

def save_clan_data(clan_data: dict):
    filepath = os.path.join(CLANS_DIR, f"{clan_data['name'].lower()}.txt")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"name={clan_data['name']}\n")
        f.write(f"owner={clan_data['owner']}\n")
        f.write(f"bank={clan_data['bank']}\n")
        f.write(f"members={','.join(map(str, clan_data['members']))}\n")

def parse_dice_value(value: int) -> list:
    v = value - 1
    s1 = v % 4
    s2 = (v // 4) % 4
    s3 = (v // 16) % 4
    mapping = {0: "BAR", 1: "SLIVKA", 2: "LEMON", 3: "SEVEN"}
    return [mapping[s1], mapping[s2], mapping[s3]]

@dp.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject):
    user_id = message.from_user.id
    user_data = load_user_data(user_id)
    user_data["name"] = message.from_user.first_name

    # Обробка рефералки
    if command.args and not user_data["referrer"]:
        try:
            ref_id = int(command.args)
            if ref_id != user_id:
                ref_data = load_user_data(ref_id)
                ref_data["balance"] += 2000.0
                ref_data["ref_count"] += 1
                save_user_data(ref_id, ref_data)
                user_data["referrer"] = str(ref_id)
                user_data["balance"] += 1000.0
        except ValueError:
            pass

    save_user_data(user_id, user_data)
    await message.answer(f"🎰 Добро пожаловать в Казино Бот, {message.from_user.first_name}!\n💰 Баланс: {user_data['balance']:.1f}$\n💡 Напишите «помощь» для меню.")

# --- МЕНЮ ПОМОЩИ З ІНТЕРАКТИВНИМИ КНОПКАМИ ---
def get_help_keyboard():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Игры", callback_data="help_games"),
         InlineKeyboardButton(text="💼 Экономика", callback_data="help_eco")],
        [InlineKeyboardButton(text="🏦 Банк & Промо", callback_data="help_bank"),
         InlineKeyboardButton(text="👑 Титулы & Рынок", callback_data="help_titles")],
        [InlineKeyboardButton(text="🛡 Кланы & Топ", callback_data="help_clans")]
    ])
    return kb

@dp.message(F.text.lower().in_(["помощь", "хелп", "команды"]))
async def show_help(message: Message):
    text = "📜 **ГЛАВНОЕ МЕНЮ ПОМОЩИ**\nВыберите интересующий раздел ниже:"
    await message.answer(text, reply_markup=get_help_keyboard())

@dp.callback_query(F.data.startswith("help_"))
async def process_help_callback(callback: CallbackQuery):
    section = callback.data.split("_")[1]
    if section == "games":
        text = ("🎮 **ИГРЫ:**\n"
                "• `рулетка` — открыть лобби рулетки (от 2 игроков в чате)\n"
                "• `казино` — крутить слот (100$)\n"
                "• `баскет` / `фут` / `дартс` / `боул` — миниигры (100$)")
    elif section == "eco":
        text = ("💼 **ЭКОНОМИКА:**\n"
                "• `бонус` — ежедневный бонус и шанс титула\n"
                "• `работа` — подработка (раз в 10 мин)\n"
                "• `баланс` или `б` — ваш профиль\n"
                "• `купить` — магазин бизнесов\n"
                "• `перевод [ID] [сумма]` — перевести деньги\n"
                "• `пригласить` — получить реф. ссылку")
    elif section == "bank":
        text = ("🏦 **БАНК И ПРОМОКОДЫ:**\n"
                "• `банк пополнить [сумма]` — положить (+1% каждые 4 часа)\n"
                "• `банк снять [сумма]` — снять из банка\n"
                "• `промо [код]` — активировать промокод")
    elif section == "titles":
        text = ("👑 **ТИТУЛЫ И РЫНОК:**\n"
                "• `мои титулы` — посмотреть свои титулы\n"
                "• `рынок` — рынок титулов игроков и системных\n"
                "• `продать титул [название] [цена]` — выставить титул\n"
                "• `купить титул [ID]` — купить титул игрока\n"
                "• `купить спец [название]` — эксклюзивный титул")
    elif section == "clans":
        text = ("🛡 **КЛАНЫ И ТОП:**\n"
                "• `создать клан [название]` — (50,000$)\n"
                "• `вступить [название]` / `покинуть`\n"
                "• `топ` — рейтинг богатейших игроков чата/бота")
    await callback.message.edit_text(text, reply_markup=get_help_keyboard())
    await callback.answer()

# --- ТОП ТА ПРИГЛАСИТЬ ---
@dp.message(F.text.lower() == "пригласить")
async def invite_cmd(message: Message):
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={message.from_user.id}"
    await message.answer(
        f"📩 **Реферальная программа:**\n"
        f"Отправьте ссылку другу: `{ref_link}`\n\n"
        f"🎁 Вы получите +2,000$, а ваш друг +1,000$!"
    )

@dp.message(F.text.lower() == "топ")
async def top_cmd(message: Message):
    users = []
    for filename in os.listdir(USERS_DIR):
        if filename.endswith(".txt"):
            u_id = filename.replace(".txt", "")
            data = load_user_data(int(u_id))
            total_money = data["balance"] + data["bank"]
            users.append((data["name"], total_money))

    users.sort(key=lambda x: x[1], reverse=True)
    top_text = "🏆 **ТОП 10 БОГАТЕЙШИХ ИГРОКОВ:**\n\n"
    for i, (name, total) in enumerate(users[:10], start=1):
        top_text += f"{i}. **{name}** — {total:,.1f}$\n"

    await message.answer(top_text)

# --- БАНК (+1% КОЖНІ 4 ГОДИНИ) ---
@dp.message(F.text.lower().startswith("банк"))
async def bank_cmd(message: Message):
    parts = message.text.split()
    user_id = message.from_user.id
    data = load_user_data(user_id)

    if len(parts) == 1:
        await message.answer(
            f"🏦 Ваш банк: **{data['bank']:.1f}$**\n"
            f"(Приносит +1% каждые 4 часа)\n\n"
            f"Команды:\n• `банк пополнить [сумма]`\n• `банк снять [сумма]`"
        )
        return

    action = parts[1].lower()
    if len(parts) < 3 or not parts[2].isdigit():
        await message.answer("❌ Укажите сумму цифрами!")
        return

    amount = float(parts[2])
    if amount <= 0: return

    if action in ["пополнить", "положить"]:
        if data["balance"] < amount:
            await message.answer("❌ Недостаточно наличных средств!")
            return
        data["balance"] -= amount
        data["bank"] += amount
        save_user_data(user_id, data)
        await message.answer(f"✅ Вы положили в банк {amount:.1f}$. Баланс банка: {data['bank']:.1f}$")
    elif action in ["снять", "забрать"]:
        if data["bank"] < amount:
            await message.answer("❌ Недостаточно средств в банке!")
            return
        data["bank"] -= amount
        data["balance"] += amount
        save_user_data(user_id, data)
        await message.answer(f"✅ Вы сняли из банка {amount:.1f}$. Наличные: {data['balance']:.1f}$")

# --- ПРОМОКОДИ ---
@dp.message(F.text.lower().startswith("создать промо"))
async def create_promo_cmd(message: Message):
    if message.from_user.id != 6663798088:
        await message.answer("❌ Эта команда доступна только владельцу бота (@nemcheni)!")
        return

    parts = message.text.split()
    if len(parts) < 4:
        await message.answer("❌ Формат: `создать промо [название] [деньги] [активации]`")
        return

    code = parts[2]
    try:
        money = float(parts[3])
        uses = int(parts[4])
    except ValueError:
        await message.answer("❌ Некорректные числа!")
        return

    promos = load_promos()
    promos[code] = {"money": money, "uses": uses}
    save_promos(promos)
    await message.answer(f"✅ Промокод `{code}` на {money}$ ({uses} активаций) успешно создан!")

@dp.message(F.text.lower().startswith("промо"))
async def use_promo_cmd(message: Message):
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("❌ Введите код: `промо [название]`")
        return

    code = parts[1]
    user_id = message.from_user.id
    data = load_user_data(user_id)

    if code in data["used_promos"]:
        await message.answer("❌ Вы уже активировали этот промокод!")
        return

    promos = load_promos()
    if code not in promos or promos[code]["uses"] <= 0:
        await message.answer("❌ Промокод не существует или закончился!")
        return

    reward = promos[code]["money"]
    data["balance"] += reward
    data["used_promos"].append(code)
    save_user_data(user_id, data)

    promos[code]["uses"] -= 1
    if promos[code]["uses"] <= 0:
        del promos[code]
    save_promos(promos)

    await message.answer(f"🎉 Промокод активирован! Вы получили +{reward:.1f}$")

# --- БОНУС ТА ТИТУЛИ ---
@dp.message(F.text.lower() == "бонус")
async def get_daily_bonus(message: Message):
    user_id = message.from_user.id
    data = load_user_data(user_id)
    now = time.time()

    if now - data["last_bonus"] < 86400:
        left_sec = int(86400 - (now - data["last_bonus"]))
        await message.answer(f"⏳ Следующий бонус через: {left_sec // 3600}ч {(left_sec % 3600) // 60}мин!")
        return

    bonus = random.randint(500, 5000)
    data["balance"] += bonus
    data["last_bonus"] = now

    msg_text = f"🎁 Ежедневный бонус: +{bonus}$!\n"

    # Шанс выпадения титула (30%)
    if random.random() < 0.3:
        rand_val = random.random()
        if rand_val < 0.5: rarity = "Обычный"
        elif rand_val < 0.75: rarity = "Редкий"
        elif rand_val < 0.90: rarity = "Эпический"
        elif rand_val < 0.98: rarity = "Легендарный"
        else: rarity = "Мифический"

        available = [t_name for t_name, t_info in TITLES_DB.items() if t_info["rarity"] == rarity]
        got_title = random.choice(available)

        if got_title not in data["titles"]:
            data["titles"].append(got_title)
            msg_text += f"🎉 **ВАМ ВЫПАЛ ТИТУЛ:** [{rarity}] {got_title}!\n"

            info = TITLES_DB[got_title]
            if info["reward_type"] == "money":
                data["balance"] += info["val"]
                msg_text += f"🎁 Награда титула: +{info['val']}$\n"
            elif info["reward_type"] == "biz":
                biz_name = info["val"]
                data["businesses"][biz_name] = data["businesses"].get(biz_name, 0) + 1
                msg_text += f"🎁 Награда титула: бизнес {biz_name.capitalize()}!\n"

    save_user_data(user_id, data)
    await message.answer(msg_text + f"💰 Баланс: {data['balance']:.1f}$")

@dp.message(F.text.lower() == "мои титулы")
async def my_titles(message: Message):
    data = load_user_data(message.from_user.id)
    if not data["titles"]:
        await message.answer("📜 У вас пока нет титулов. Выбивайте их в `бонус`!")
        return

    res = "👑 **Ваши титулы:**\n"
    for t in data["titles"]:
        if t in TITLES_DB:
            r = TITLES_DB[t]["rarity"]
            d = TITLES_DB[t]["desc"]
            res += f"• **{t}** [{r}] — {d}\n"
        else:
            res += f"• **{t}** [Специальный]\n"
    await message.answer(res)

# --- РЫНОК ТИТУЛОВ ---
@dp.message(F.text.lower() == "рынок")
async def show_market(message: Message):
    items = load_market()
    text = "🛒 **РЫНОК ТИТУЛОВ ИГРОКОВ:**\n\n"
    if not items:
        text += "Рынок пуст.\n"
    else:
        for it in items:
            text += f"🆔 `{it['id']}` | **{it['title']}** — {it['price']:.1f}$ (Продавец: `{it['seller_id']}`)\n"

    text += "\n⭐ **СПЕЦИАЛЬНЫЕ ТИТУЛЫ ОТ ИГРЫ:**\n"
    for st_name, st_info in SYSTEM_TITLES.items():
        text += f"• **{st_name}** — {st_info['price']:,}$ (`купить спец {st_name}`)\n"

    text += "\n💡 Команды: `продать титул [название] [цена]`, `купить титул [ID]`"
    await message.answer(text)

@dp.message(F.text.lower().startswith("продать титул"))
async def sell_title(message: Message):
    parts = message.text.split(maxsplit=3)
    if len(parts) < 4 or not parts[3].isdigit():
        await message.answer("❌ Формат: `продать титул [название] [цена]`")
        return

    title_name = parts[2]
    price = float(parts[3])
    user_id = message.from_user.id
    data = load_user_data(user_id)

    if title_name not in data["titles"]:
        await message.answer("❌ У вас нет такого титула!")
        return

    data["titles"].remove(title_name)
    save_user_data(user_id, data)

    items = load_market()
    item_id = random.randint(1000, 9999)
    items.append({"id": item_id, "seller_id": user_id, "title": title_name, "price": price})
    save_market(items)

    await message.answer(f"✅ Титул **{title_name}** выставлен на рынок за {price}$ (ID: `{item_id}`)!")

@dp.message(F.text.lower().startswith("купить титул"))
async def buy_title(message: Message):
    parts = message.text.split()
    if len(parts) < 3 or not parts[2].isdigit():
        await message.answer("❌ Укажите ID: `купить титул [ID]`")
        return

    item_id = int(parts[2])
    items = load_market()
    item = next((i for i in items if i["id"] == item_id), None)

    if not item:
        await message.answer("❌ Товар не найден на рынке!")
        return

    buyer_id = message.from_user.id
    buyer_data = load_user_data(buyer_id)

    if buyer_data["balance"] < item["price"]:
        await message.answer("❌ Недостаточно средств!")
        return

    buyer_data["balance"] -= item["price"]
    buyer_data["titles"].append(item["title"])
    save_user_data(buyer_id, buyer_data)

    seller_data = load_user_data(item["seller_id"])
    seller_data["balance"] += item["price"]
    save_user_data(item["seller_id"], seller_data)

    items.remove(item)
    save_market(items)

    await message.answer(f"🎉 Вы успешно купили титул **{item['title']}**!")

@dp.message(F.text.lower().startswith("купить спец"))
async def buy_system_title(message: Message):
    title_name = message.text[12:].strip()
    if title_name not in SYSTEM_TITLES:
        await message.answer("❌ Такого специального титула нет!")
        return

    price = SYSTEM_TITLES[title_name]["price"]
    user_id = message.from_user.id
    data = load_user_data(user_id)

    if title_name in data["titles"]:
        await message.answer("❌ У вас уже есть этот титул!")
        return

    if data["balance"] < price:
        await message.answer(f"❌ Нужно {price:,}$!")
        return

    data["balance"] -= price
    data["titles"].append(title_name)
    save_user_data(user_id, data)
    await message.answer(f"👑 Поздравляем! Вы приобрели эксклюзивный титул **{title_name}**!")

# --- РУЛЕТКА ДЛЯ ЧАТІВ (БЕЗ СОЛО) ---
def get_roulette_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="⏳ +30 сек", callback_data="r_add_time"),
        InlineKeyboardButton(text="🚀 Начать", callback_data="r_start_now")
    ]])

@dp.message(F.text.lower() == "рулетка")
async def init_roulette(message: Message):
    if message.chat.type == "private":
        await message.answer("❌ Играть в рулетку в соло нельзя! Она доступна только в групповых чатах.")
        return

    chat_id = message.chat.id
    if chat_id in roulette_lobbies:
        await message.answer("❌ В этом чате уже идет набор в рулетку!")
        return

    roulette_lobbies[chat_id] = {
        "end_time": time.time() + 120,
        "players": {},
        "task": None
    }

    msg = await message.answer(
        "🎰 **ОТКРЫТ НАБОР В РУЛЕТКУ!**\n\n"
        "⏳ Набор длится 2 минуты (минимум 2 игрока).\n"
        "Делайте ставки командой:\n`ставка [красное/черное/0-36] [сумма]`",
        reply_markup=get_roulette_kb()
    )

    task = asyncio.create_task(roulette_timer(chat_id, msg.message_id))
    roulette_lobbies[chat_id]["task"] = task

@dp.message(F.text.lower().startswith("ставка"))
async def place_roulette_bet(message: Message):
    chat_id = message.chat.id
    if chat_id not in roulette_lobbies:
        await message.answer("❌ Набор в рулетку сейчас не идет! Напишите `рулетка`")
        return

    parts = message.text.split()
    if len(parts) < 3:
        await message.answer("❌ Формат: `ставка [красное/черное/0-36] [сумма]`")
        return

    choice = parts[1].lower()
    try:
        bet = float(parts[2])
    except ValueError:
        await message.answer("❌ Некорректная сумма!")
        return

    user_id = message.from_user.id
    data = load_user_data(user_id)

    if bet <= 0 or data["balance"] < bet:
        await message.answer("❌ Недостаточно средств!")
        return

    data["balance"] -= bet
    save_user_data(user_id, data)

    roulette_lobbies[chat_id]["players"][user_id] = {
        "name": message.from_user.first_name,
        "choice": choice,
        "bet": bet
    }
    await message.answer(f"✅ {message.from_user.first_name} сделал ставку {bet}$ на **{choice}**!")

@dp.callback_query(F.data.startswith("r_"))
async def handle_roulette_buttons(callback: CallbackQuery):
    chat_id = callback.message.chat.id
    if chat_id not in roulette_lobbies:
        await callback.answer("Лобби устарело.", show_alert=True)
        return

    if callback.data == "r_add_time":
        roulette_lobbies[chat_id]["end_time"] += 30
        await callback.answer("Добавлено +30 секунд!")
        await callback.message.edit_text(
            f"🎰 **НАБОР В РУЛЕТКУ ПРОДЛЕН!**\nУчастников: {len(roulette_lobbies[chat_id]['players'])}\nСтавки: `ставка [выбор] [сумма]`",
            reply_markup=get_roulette_kb()
        )
    elif callback.data == "r_start_now":
        if len(roulette_lobbies[chat_id]["players"]) < 2:
            await callback.answer("❌ Нужно минимум 2 игрока со ставками!", show_alert=True)
            return
        roulette_lobbies[chat_id]["end_time"] = time.time()
        await callback.answer("Запускаем!")

async def roulette_timer(chat_id: int, message_id: int):
    while True:
        await asyncio.sleep(2)
        if chat_id not in roulette_lobbies: return
        if time.time() >= roulette_lobbies[chat_id]["end_time"]:
            break

    lobby = roulette_lobbies[chat_id]
    players = lobby["players"]

    if len(players) < 2:
        for u_id, p_info in players.items():
            u_data = load_user_data(u_id)
            u_data["balance"] += p_info["bet"]
            save_user_data(u_id, u_data)
        await bot.send_message(chat_id, "❌ Рулетка отменена: не набралось 2 участника. Ставки возвращены.")
        del roulette_lobbies[chat_id]
        return

    number = random.randint(0, 36)
    color = "зеленое" if number == 0 else ("красное" if number in RED_NUMBERS else "черное")

    res_text = f"🎰 **РУЛЕТКА СФОРМИРОВАНА!**\nВыпало: **{number} ({color})**!\n\n**Результаты:**\n"

    for u_id, p in players.items():
        win = 0
        if p["choice"] in ["красное", "черное"] and p["choice"] == color:
            win = p["bet"] * 2
        elif p["choice"].isdigit() and int(p["choice"]) == number:
            win = p["bet"] * 36

        u_data = load_user_data(u_id)
        u_data["balance"] += win
        save_user_data(u_id, u_data)

        if win > 0:
            res_text += f"🎉 {p['name']} выиграл +{win:.1f}$!\n"
        else:
            res_text += f"❌ {p['name']} проиграл {p['bet']:.1f}$\n"

    await bot.send_message(chat_id, res_text)
    del roulette_lobbies[chat_id]

# --- ПОНЕРФЛЕНЕ КАЗИНО ---
@dp.message(F.text.lower() == "казино")
async def spin_casino(message: Message):
    user_id = message.from_user.id
    data = load_user_data(user_id)

    if data["balance"] < 100:
        await message.answer("❌ Недостаточно средств! Игра стоит 100$.")
        return

    data["balance"] -= 100
    save_user_data(user_id, data)

    msg = await message.answer_dice(emoji="🎰")
    symbols = parse_dice_value(msg.dice.value)
    await asyncio.sleep(2)

    counts = {}
    for s in symbols:
        counts[s] = counts.get(s, 0) + 1

    total_win = 0
    symbols_ru = {"BAR": "BAR", "SLIVKA": "Сливка", "LEMON": "Лимон", "SEVEN": "Семерка"}
    result_text = []

    for sym, count in counts.items():
        base_val = SYMBOL_VALUES[sym]
        if count == 1:
            win = base_val  # Понерфлено у 2 рази для одиночних
        elif count == 2:
            win = 2 * (2 * (base_val * 2))  # Без нерфу (Бонус)
        elif count == 3:
            win = 3 * (3 * (base_val * 2))  # Без нерфу (Бонус)
        total_win += win
        result_text.append(f"{count}x {symbols_ru[sym]}")

    data["balance"] += total_win
    save_user_data(user_id, data)

    out = (
        f"🎰 Выпало: {', '.join(result_text)}\n"
        f"🎉 Выигрыш: +{total_win}$\n"
        f"💰 Новый баланс: {data['balance']:.1f}$"
    )
    await message.answer(out)

# --- РЕШТА МІНІ-ІГОР ---
@dp.message(F.text.lower() == "баскет")
async def play_basket(message: Message):
    user_id = message.from_user.id
    data = load_user_data(user_id)
    if data["balance"] < 100: return
    data["balance"] -= 100
    msg = await message.answer_dice(emoji="🏀")
    await asyncio.sleep(3)
    val = msg.dice.value
    win = 200 if val in [4, 5] else (500 if val == 6 else 0)
    data["balance"] += win
    save_user_data(user_id, data)
    await message.answer(f"🎉 Выигрыш: +{win}$\n💰 Баланс: {data['balance']:.1f}$")

@dp.message(F.text.lower() == "фут")
async def play_football(message: Message):
    user_id = message.from_user.id
    data = load_user_data(user_id)
    if data["balance"] < 100: return
    data["balance"] -= 100
    msg = await message.answer_dice(emoji="⚽")
    await asyncio.sleep(3)
    win = 250 if msg.dice.value in [3, 4, 5] else 0
    data["balance"] += win
    save_user_data(user_id, data)
    await message.answer(f"🎉 Выигрыш: +{win}$\n💰 Баланс: {data['balance']:.1f}$")

@dp.message(F.text.lower() == "дартс")
async def play_darts(message: Message):
    user_id = message.from_user.id
    data = load_user_data(user_id)
    if data["balance"] < 100: return
    data["balance"] -= 100
    msg = await message.answer_dice(emoji="🎯")
    await asyncio.sleep(3)
    win = 200 if msg.dice.value in [2, 3, 4, 5] else (500 if msg.dice.value == 6 else 0)
    data["balance"] += win
    save_user_data(user_id, data)
    await message.answer(f"🎉 Выигрыш: +{win}$\n💰 Баланс: {data['balance']:.1f}$")

@dp.message(F.text.lower() == "боул")
async def play_bowling(message: Message):
    user_id = message.from_user.id
    data = load_user_data(user_id)
    if data["balance"] < 100: return
    data["balance"] -= 100
    msg = await message.answer_dice(emoji="🎳")
    await asyncio.sleep(3)
    win = 200 if msg.dice.value in [3, 4, 5] else (600 if msg.dice.value == 6 else 0)
    data["balance"] += win
    save_user_data(user_id, data)
    await message.answer(f"🎉 Выигрыш: +{win}$\n💰 Баланс: {data['balance']:.1f}$")

@dp.message(F.text.lower().in_(["баланс", "б"]))
async def show_balance(message: Message):
    data = load_user_data(message.from_user.id)
    text = f"💳 Наличные: {data['balance']:.1f}$\n🏦 Банк: {data['bank']:.1f}$\n🆔 Ваш ID: `{message.from_user.id}`\n"
    if data["clan"]: text += f"🛡 Клан: {data['clan']}\n"
    text += "\n🏢 Бизнесы:\n" + ("У вас нет бизнесов." if not data["businesses"] else "\n".join([f"• {b.capitalize()}: {c} шт." for b, c in data["businesses"].items()]))
    await message.answer(text)

@dp.message(F.text.lower() == "работа")
async def do_work(message: Message):
    user_id = message.from_user.id
    data = load_user_data(user_id)
    now = time.time()
    if now - data["last_work"] < 600:
        await message.answer(f"⏳ Отдохните ещё {int(600 - (now - data['last_work']))} сек.")
        return
    earned = random.randint(100, 800)
    data["balance"] += earned
    data["last_work"] = now
    save_user_data(user_id, data)
    await message.answer(f"🔨 Вы подработали и получили +{earned}$!")

@dp.message(F.text.lower().startswith("перевод"))
async def transfer_money(message: Message):
    parts = message.text.split()
    if len(parts) < 3 or not parts[1].isdigit(): return
    target_id, amount = int(parts[1]), float(parts[2])
    sender_id = message.from_user.id
    if sender_id == target_id or amount <= 0: return
    sender_data = load_user_data(sender_id)
    if sender_data["balance"] < amount: return
    target_data = load_user_data(target_id)
    sender_data["balance"] -= amount
    target_data["balance"] += amount
    save_user_data(sender_id, sender_data)
    save_user_data(target_id, target_data)
    await message.answer(f"✅ Перевод {amount:.1f}$ игроку `{target_id}` выполнен!")

@dp.message(F.text.lower().startswith("создать клан"))
async def create_clan(message: Message):
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3: return
    clan_name, user_id = parts[2].strip(), message.from_user.id
    data = load_user_data(user_id)
    if data["clan"] or data["balance"] < 50000 or load_clan_data(clan_name): return
    data["balance"] -= 50000
    data["clan"] = clan_name
    save_user_data(user_id, data)
    save_clan_data({"name": clan_name, "owner": user_id, "bank": 0.0, "members": [user_id]})
    await message.answer(f"🛡 Клан **{clan_name}** создан!")

@dp.message(F.text.lower().startswith("купить"))
async def buy_business(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) == 1:
        await message.answer("🛍 Покупка бизнесов:\n" + "\n".join([f"• {b.capitalize()} — {p}$" for b, (p, i) in BUSINESSES.items()]))
        return
    biz_name = parts[1].lower()
    if biz_name not in BUSINESSES: return
    price, income = BUSINESSES[biz_name]
    user_id = message.from_user.id
    data = load_user_data(user_id)
    if data["balance"] < price: return
    data["balance"] -= price
    data["businesses"][biz_name] = data["businesses"].get(biz_name, 0) + 1
    save_user_data(user_id, data)
    await message.answer(f"✅ Куплен бизнес {biz_name.capitalize()}!")

# --- ФОНОВІ ТАСКИ (БАНК +1% НА 4 ГОДИНИ ТА БІЗНЕСИ) ---
async def background_tasks():
    bank_timer = 0
    while True:
        await asyncio.sleep(3600)  # Перевірка щогодини
        bank_timer += 1
        for filename in os.listdir(USERS_DIR):
            if filename.endswith(".txt"):
                try:
                    u_id = int(filename.replace(".txt", ""))
                    data = load_user_data(u_id)

                    # Дохід від бізнесу щогодини
                    inc = sum(BUSINESSES[b][1] * c for b, c in data["businesses"].items() if b in BUSINESSES)
                    if inc > 0: data["balance"] += inc

                    # Дохід від банку +1% кожні 4 години
                    if bank_timer >= 4:
                        if data["bank"] > 0:
                            data["bank"] += data["bank"] * 0.01

                    save_user_data(u_id, data)
                except Exception:
                    pass
        if bank_timer >= 4:
            bank_timer = 0

async def main():
    asyncio.create_task(background_tasks())
    print("Бот успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
