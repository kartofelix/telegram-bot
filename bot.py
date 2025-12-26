import re
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import Command
from datetime import datetime, timedelta
from config import BOT_TOKEN
from db import (
    ACHIEVEMENTS,
    ACHIEVEMENT_DESCRIPTIONS,
    get_top_swear_users,
    get_top_swearers_last_week,
    top_swearers_week,
    get_swear_stats,
    get_message_count,
    has_achievement,
    add_achievement,
    get_user_achievements,
    log_message,
    log_swear,
    top_users_with_total,
    can_give_rep,
    add_rep,
    get_rep,
)

# ================== BOT ==================
import os
from config import BOT_TOKEN, CHAT_ID
from aiogram import Bot, Dispatcher

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

# ================== АВТОПОСТ ==================
def seconds_until_next_monday():
    now = datetime.utcnow()

    # weekday(): понеділок = 0, неділя = 6
    days_ahead = (7 - now.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7  # якщо вже понеділок — беремо наступний

    next_monday = datetime(
        year=now.year,
        month=now.month,
        day=now.day,
        hour=0,
        minute=0,
        second=0
    ) + timedelta(days=days_ahead)

    return (next_monday - now).total_seconds()

async def weekly_topbad_autopost():
    await asyncio.sleep(seconds_until_next_monday())

    while True:
        # 🔥 ТУТ ТИ МОЖЕШ ЗАМІНИТИ chat_id НА СВІЙ
        CHAT_ID = int(os.getenv("CHAT_ID"))

        # беремо минулі 7 днів
        users = get_top_swear_users(CHAT_ID, days=7)

        if users:
            text = "🔥 <b>Топ матюкарів за тиждень:</b>\n\n"
            for i, (username, count) in enumerate(users, 1):
                text += f"{i}. {username} — {count}\n"

            winner = users[0]
            text += f"\n🏆 <b>Петух тижня:</b>\n{winner[0]} — Пиздів як бог"

            await bot.send_message(CHAT_ID, text, parse_mode="HTML")

        # 💤 СПИМО РІВНО 7 ДНІВ
        await asyncio.sleep(7 * 24 * 60 * 60)

# ================== НАСТРОЙКИ ==================
BAD_REGEX = re.compile(
    r"|".join(BAD_PATTERNS),
    flags=re.IGNORECASE
)

SPECIAL_420_USER_ID = 7154333160 # ID для очівки 420

REP_PLUS = {"+", "реп", "зов"}
REP_MINUS = {"-", "не реп", "хуйня"}

PREFIX = r"(за|ви|на|пере|по|про|об|від|у|з|с)?"
SUFFIX = r"[а-яіїєґ]*"

BAD_PATTERNS = [
    rf"\b{PREFIX}ху(й|йом|лі|їла|йня|йло|йняк|йовий|єглот|єглотка|єсос|єсоска|йлан|йланка|єсосіна|ярилися|ярились|хуяримо|йліна){SUFFIX}\b",
    rf"\b{PREFIX}пизд(а|ец|ёж|юк|ити|ець|ите|ун|уняр|уняра|олиз|олизка|унка|уй|ос){SUFFIX}\b",
    rf"\b{PREFIX}пізд(а|ец|юк|ити|ець|ите|ун|уняр|уняра|олиз|олизка|унка|уй|ос){SUFFIX}\b",
    rf"\b{PREFIX}пезд(а|ец|юк|ити|ець|ите|ун|уняр|уняра|олиз|олизка|унка|уй|олиз|ос|или){SUFFIX}\b",
    rf"\b{PREFIX}[єеї]б(а|ать|нути|ан|лан|нутись|ат|анутись|анути|ланоїд|ланка|лун|батись|балися|батися|бались){SUFFIX}\b",
    rf"\b{PREFIX}бля(дь|ха|діна|дина|ть|т|буду|дота){SUFFIX}\b",
    rf"\b{PREFIX}с(ука|учка|учара|хуялі|пиздимся|пиздлись|пиздимося|пиздимось|пиздилися|хуйнувся|дрочився|хуйнулися|хуйнулись|дрочилися|дрочився|пиздив|пиздила)?{SUFFIX}\b",
    rf"\b{PREFIX}на(хуй|хуя|хуярився|хуйнувся|єбнувся|єбнулась|дрочився|дрочив|хуярились|хуяримся|хуярилися|хуярили|хуячим|хуячимся|дрочим|дрочимо|дрочили|пиздила|пиздили|пиздився|пиздівся|бнувся|бнулися|бнулась|бнулася|бнувся|бнулись|бнулася|бнулась|залупі){SUFFIX}\b",
    rf"\b{PREFIX}під(ар|ор|арас|орас|ріла|р|рілка|арасіна|арасина|ріста|риста){SUFFIX}\b",
    rf"\b{PREFIX}пид(ар|ор|арас|орас|ріла|р|рілка|арасина|арасіна|ріста|риста){SUFFIX}\b",
    rf"\b{PREFIX}уйобок{SUFFIX}\b",
    rf"\b{PREFIX}ган(дон|дурас|дончик|дурасик|дончик){SUFFIX}\b",
    rf"\b{PREFIX}шл(юшка|юха|ендра|ьондра|ёндра){SUFFIX}\b",
    rf"\b{PREFIX}шалава{SUFFIX}\b",
    rf"\b{PREFIX}за(їбався|ебался|ебався|єбав|ебав|лупа|лупівка|лупка){SUFFIX}\b",
    rf"\b{PREFIX}по(хуярили|хуячим|дрочим|хуярим|хуяримо|дрочили|дрочимо|хуячимся|пиздився|хуячили|залупі){SUFFIX}",
]

BAD_REGEX = re.compile("|".join(BAD_PATTERNS), re.IGNORECASE)

def contains_bad_words(text: str) -> bool:
    text = text.lower()
    return any(re.search(p, text) for p in BAD_PATTERNS)

# ================== КОМАНДИ ==================

@dp.message(Command("commandss"), F.chat.type.in_({"group", "supergroup"}))
async def commands(msg: Message):
    await msg.answer(
        "📖 <b>Команди</b>\n\n"
        "/stats — вся статистика\n"
        "/stats_day — за 24 години\n"
        "/stats_week — за 7 днів\n\n"
        "⭐ Реп через відповідь:\n"
        "+ / реп / зов\n"
        "- / не реп / хуйня\n\n"
        "/achievementss — твої очівки",
        parse_mode="HTML"
    )
#/stats /stats_day /stats_week
@dp.message(Command("stats"), F.chat.type.in_({"group", "supergroup"}))
async def stats_all(msg: Message):
    users, total = top_users_with_total(msg.chat.id, 10_000)

    if not users:
        await msg.answer("Даних нема")
        return

    text = "📊 <b>За весь час</b>\n\n"
    for i, (username, count) in enumerate(users, 1):
        text += f"{i}. {username} — {count}\n"

    text += f"\n💬 Всього: {total}"
    await msg.answer(text, parse_mode="HTML")


@dp.message(Command("stats_day"), F.chat.type.in_({"group", "supergroup"}))
async def stats_day(msg: Message):
    users, total = top_users_with_total(msg.chat.id, 24)

    if not users:
        await msg.answer("Даних за день нема")
        return

    text = "📅 <b>За 24 години</b>\n\n"
    for i, (username, count) in enumerate(users, 1):
        text += f"{i}. {username} — {count}\n"

    text += f"\n💬 Всього: {total}"
    await msg.answer(text, parse_mode="HTML")


@dp.message(Command("stats_week"), F.chat.type.in_({"group", "supergroup"}))
async def stats_week(msg: Message):
    users, total = top_users_with_total(msg.chat.id, 24 * 7)

    if not users:
        await msg.answer("Даних за тиждень нема")
        return

    text = "🗓 <b>За 7 днів</b>\n\n"
    for i, (username, count) in enumerate(users, 1):
        text += f"{i}. {username} — {count}\n"

    text += f"\n💬 Всього: {total}"
    await msg.answer(text, parse_mode="HTML")


#МАТЮКИ ТОП ТИЖНЯ
@dp.message(Command("topbad"), F.chat.type.in_({"group", "supergroup"}))
async def topbad(msg: Message):
    args = msg.text.split()

    if len(args) < 2 or args[1] != "week":
        await msg.answer("Юзай: /topbad week")
        return

    rows, start, end = get_top_swearers_last_week(msg.chat.id)

    if not rows:
        await msg.answer(
            "❌ Дані за минулий тиждень ще не сформовані посмокчіть хуй і почекайте\n"
            "Матюки зараз збираються 😈"
        )
        return

    text = "🔥 <b>Топ матюкарів за тиждень:</b>\n\n"

    for i, (username, count) in enumerate(rows, 1):
        text += f"{i}. {username} — {count}\n"

    winner = rows[0][0]

    text += (
        "\n🏆 <b>Переможець тижня:</b>\n"
        f"{winner} — Пиздів як бог"
    )

    await msg.answer(text, parse_mode="HTML")


#ПРИВАТНА КОМАНДА в боті
@dp.message(Command("bad_debug"))
async def bad_debug(msg: Message):

    if msg.chat.type != "private":
        return

               # ID chat
    CHAT_ID = int(os.getenv("CHAT_ID"))

    users, total = get_swear_stats(CHAT_ID, days=7)

    if not users:
        await msg.answer("❌ За цей тиждень матюків ще нема")
        return

    text = "🤬 <b>Матюки за поточний тиждень:</b>\n\n"
    for i, (username, count) in enumerate(users, 1):
        text += f"{i}. {username} — {count}\n"

    text += f"\n<b>Всього:</b> {total}"
    await msg.answer(text, parse_mode="HTML")

# ================== РЕПУТАЦІЯ ==================

@dp.message(F.reply_to_message, F.text, F.chat.type.in_({"group", "supergroup"}))
async def reputation_handler(msg: Message):
    text = msg.text.lower().strip()
    if text not in REP_PLUS and text not in REP_MINUS:
        return

    from_user = msg.from_user.id
    to_user = msg.reply_to_message.from_user.id

    if from_user == to_user:
        return

    if not can_give_rep(msg.chat.id, from_user, to_user):
        await msg.answer("⛔ Підр ти вже давав реп цій свині жирній")
        return

    value = 1 if text in REP_PLUS else -1
    add_rep(msg.chat.id, from_user, to_user, value)

    plus, minus = get_rep(msg.chat.id, to_user)
    await msg.answer(f"⭐ Реп оновлено\n+{plus} / -{minus}")

# ================== ОЧІВКИ ==================

@dp.message(Command("achievementss"), F.chat.type.in_({"group", "supergroup"}))
async def my_achievements(msg: Message):
    achs = get_user_achievements(msg.chat.id, msg.from_user.id)
    if not achs:
        await msg.answer("Хуйло в тебе ше нічого немає")
        return

    text = "🏆 <b>Твої очівки</b>\n\n"
    for i, (name, _) in enumerate(achs, 1):
        text += f"{i}. {name}\n"

    await msg.answer(text, parse_mode="HTML")

# ================== ЛОГ ВСЬОГО ==================

@dp.message(F.chat.type.in_({"group", "supergroup"}))
async def log_all_messages(msg: Message):
    if not msg.from_user:
        return

    chat_id = msg.chat.id
    user_id = msg.from_user.id
    username = msg.from_user.username or msg.from_user.first_name
    text = msg.text or ""

    # 🔥 1. ЛОГУЄМО МАТЮКИ (ЗАВЖДИ)
if text:
    bad_count = len(BAD_REGEX.findall(text))
    if bad_count > 0:
        log_swear(chat_id, user_id, username, bad_count)

    # ❌ НЕ РАХУЄМО КОМАНДИ ЯК ПОВІДОМЛЕННЯ
    if text.startswith("/"):
        return

    # 🔹 2. ЛОГУЄМО ЗВИЧАЙНЕ ПОВІДОМЛЕННЯ
    log_message(chat_id, user_id, username)

    # 🔹 3. ОЧІВКИ
    count = get_message_count(chat_id, user_id)

    for limit, title in ACHIEVEMENTS:
        if limit == 420 and user_id != SPECIAL_420_USER_ID:
            continue

        if count >= limit and not has_achievement(chat_id, user_id, title):
            add_achievement(chat_id, user_id, title)
            desc = ACHIEVEMENT_DESCRIPTIONS.get(limit, "")

            await msg.answer(
                f"🏆 <b>Нова очівка!</b>\n"
                f"<b>{title}</b>\n{desc}",
                parse_mode="HTML"
            )

# ================== START ==================

async def main():
    asyncio.create_task(weekly_topbad_autopost())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())




