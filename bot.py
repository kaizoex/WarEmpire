import random
import time
import re

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

from config import BOT_TOKEN
from database import (
    create_database,
    get_player,
    create_player,
    update_player,
)


# ==================================================
# تنظیمات بازی WarEmpire
# ==================================================

START_POINTS = 10000
START_SOLDIERS = 1000
START_TERRITORY = 10

SOLDIER_PRICE = 1500       # قیمت هر 100 سرباز
TERRITORY_PRICE = 8000     # قیمت هر 1 کیلومتر مربع

INCOME_COOLDOWN = 300      # 5 دقیقه


# ==================================================
# تجهیزات بازی
# ==================================================

MISSILES = {
    "عقاب": 3500,
    "فجر 3": 4000,
    "فجر 4": 4890,
    "فجر 5": 5500,
    "زلزال": 6600,
    "فاتح 110": 7300,
    "شهاب 1": 7800,
    "شهاب 2": 8450,
    "قادر 1": 10000,
    "شهاب 3": 12000,
    "سجیل": 18000,
}


# ==================================================
# /start
# ==================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user
    chat = update.effective_chat

    player = get_player(user.id, chat.id)

    if player:
        await update.message.reply_text(
            "🏳️ کشور تو قبلاً ساخته شده!\n\n"
            "برای دیدن وضعیت:\n"
            "وضعیت کشور"
        )
        return

    create_player(
        user_id=user.id,
        chat_id=chat.id,
        username=user.username or user.first_name,
        points=START_POINTS,
        soldiers=START_SOLDIERS,
        territory=START_TERRITORY,
    )

    await update.message.reply_text(
        "🌍 به WarEmpire خوش آمدی!\n\n"
        "🏳️ کشور تو ساخته شد.\n\n"
        f"💰 پوینت وار: {START_POINTS:,}\n"
        f"👥 سرباز: {START_SOLDIERS:,}\n"
        f"🗺️ قلمرو: {START_TERRITORY} km²\n\n"
        "برای دیدن دستورات /help را بزن."
    )


# ==================================================
# /help
# ==================================================

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = """
🌍 WarEmpire
━━━━━━━━━━━━━━

🏳️ شروع بازی
شروع بازی

📊 اطلاعات کشور
وضعیت کشور

💰 درآمد
دریافت پوینت

🚀 خرید تجهیزات
خرید موشک

👥 خرید نیرو
خرید سرباز

🗺️ خرید سرزمین
خرید قلمرو

⚔️ جنگ
حمله @username

🤝 اتحاد
اتحاد @username

💱 تجارت
داد و ستد @username

🎯 چالش
چالش

━━━━━━━━━━━━━━
/help
نمایش راهنما
"""

    await update.message.reply_text(text)


# ==================================================
# ساخت کشور با متن
# ==================================================

async def create_country(update: Update):

    user = update.effective_user
    chat = update.effective_chat

    if get_player(user.id, chat.id):

        await update.message.reply_text(
            "❌ کشور تو از قبل ساخته شده."
        )
        return

    create_player(
        user_id=user.id,
        chat_id=chat.id,
        username=user.username or user.first_name,
        points=START_POINTS,
        soldiers=START_SOLDIERS,
        territory=START_TERRITORY,
    )

    await update.message.reply_text(
        "✅ کشور با موفقیت ساخته شد!\n\n"
        f"💰 {START_POINTS:,} پوینت وار\n"
        f"👥 {START_SOLDIERS:,} سرباز\n"
        f"🗺️ {START_TERRITORY} km² قلمرو"
    )


# ==================================================
# وضعیت کشور
# ==================================================

async def country_status(update: Update):

    user = update.effective_user
    chat = update.effective_chat

    player = get_player(user.id, chat.id)

    if not player:

        await update.message.reply_text(
            "❌ اول «شروع بازی» را بزن."
        )
        return

    (
        user_id,
        chat_id,
        username,
        country,
        points,
        soldiers,
        territory,
        level,
        attacks,
        successful_attacks,
        failed_attacks,
        successful_defenses,
        failed_defenses,
        losses,
        last_income,
    ) = player

    text = f"""
🏳️ کشور: {country}

⭐ سطح: {level}/20

💰 پوینت وار: {points:,}
👥 سرباز: {soldiers:,}
🗺️ قلمرو: {territory:,} km²

⚔️ کل حملات: {attacks}
✅ حملات موفق: {successful_attacks}
❌ حملات ناموفق: {failed_attacks}

🛡️ دفاع موفق: {successful_defenses}
❌ دفاع ناموفق: {failed_defenses}

💥 شکست‌ها: {losses}/6
"""

    await update.message.reply_text(text)


# ==================================================
# دریافت پوینت
# ==================================================

async def collect_points(update: Update):

    user = update.effective_user
    chat = update.effective_chat

    player = get_player(user.id, chat.id)

    if not player:

        await update.message.reply_text(
            "❌ اول «شروع بازی» را بزن."
        )
        return

    now = int(time.time())
    last_income = player[14]

    if now - last_income < INCOME_COOLDOWN:

        remaining = INCOME_COOLDOWN - (now - last_income)

        minutes = remaining // 60
        seconds = remaining % 60

        await update.message.reply_text(
            f"⏳ هنوز آماده نیست.\n"
            f"{minutes} دقیقه و {seconds} ثانیه دیگر."
        )
        return

    amount = random.randint(10, 100)

    update_player(
        user.id,
        chat.id,
        "points",
        player[4] + amount
    )

    update_player(
        user.id,
        chat.id,
        "last_income",
        now
    )

    await update.message.reply_text(
        f"💰 +{amount} پوینت وار دریافت کردی!"
    )


# ==================================================
# فروشگاه موشک
# ==================================================

async def missile_shop(update: Update):

    keyboard = []

    for name, price in MISSILES.items():

        keyboard.append([
            InlineKeyboardButton(
                f"🚀 {name} | {price:,}",
                callback_data=f"missile:{name}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            "❌ بستن",
            callback_data="close"
        )
    ])

    await update.message.reply_text(
        "🚀 فروشگاه WarEmpire\n\n"
        "یکی از تجهیزات را انتخاب کن:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ==================================================
# خرید سرباز
# ==================================================

async def soldier_shop(update: Update):

    keyboard = [
        [
            InlineKeyboardButton(
                "+100",
                callback_data="soldier:100"
            ),
            InlineKeyboardButton(
                "+500",
                callback_data="soldier:500"
            ),
        ],
        [
            InlineKeyboardButton(
                "+1000",
                callback_data="soldier:1000"
            ),
            InlineKeyboardButton(
                "+5000",
                callback_data="soldier:5000"
            ),
        ],
        [
            InlineKeyboardButton(
                "❌ بستن",
                callback_data="close"
            )
        ]
    ]

    await update.message.reply_text(
        "👥 خرید سرباز\n\n"
        f"💰 هر 100 سرباز = {SOLDIER_PRICE:,} پوینت وار\n\n"
        "تعداد موردنظر را انتخاب کن:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ==================================================
# خرید قلمرو
# ==================================================

async def territory_shop(update: Update):

    await update.message.reply_text(
        "🗺️ خرید قلمرو\n\n"
        f"💰 قیمت هر 1 km² = {TERRITORY_PRICE:,} پوینت وار\n\n"
        "مثال:\n"
        "خرید قلمرو 5\n\n"
        "یعنی خرید 5 کیلومتر مربع."
    )


# ==================================================
# خرید قلمرو با مقدار
# ==================================================

async def buy_territory(update: Update, amount):

    user = update.effective_user
    chat = update.effective_chat

    player = get_player(user.id, chat.id)

    if not player:
        await update.message.reply_text(
            "❌ اول بازی را شروع کن."
        )
        return

    if amount <= 0:
        await update.message.reply_text(
            "❌ مقدار قلمرو نامعتبر است."
        )
        return

    price = amount * TERRITORY_PRICE

    if player[4] < price:

        await update.message.reply_text(
            "❌ پوینت وار کافی نداری.\n\n"
            f"💰 نیاز: {price:,}\n"
            f"💰 موجودی: {player[4]:,}"
        )
        return

    update_player(
        user.id,
        chat.id,
        "points",
        player[4] - price
    )

    update_player(
        user.id,
        chat.id,
        "territory",
        player[6] + amount
    )

    await update.message.reply_text(
        f"✅ {amount} km² قلمرو خریداری شد!\n\n"
        f"💰 هزینه: {price:,}\n"
        f"🗺️ قلمرو جدید: {player[6] + amount:,} km²"
    )


# ==================================================
# حمله
# ==================================================

async def attack(update: Update, username):

    user = update.effective_user
    chat = update.effective_chat

    attacker = get_player(user.id, chat.id)

    if not attacker:

        await update.message.reply_text(
            "❌ اول کشور خودت را بساز."
        )
        return

    username = username.replace("@", "").lower()

    if not username:

        await update.message.reply_text(
            "❌ نام کاربر را وارد کن.\n\n"
            "مثال:\n"
            "حمله @username"
        )
        return

    target = find_player_by_username(
        chat.id,
        username
    )

    if not target:

        await update.message.reply_text(
            "❌ این بازیکن در این گروه کشور ندارد."
        )
        return

    if target[0] == attacker[0]:

        await update.message.reply_text(
            "❌ نمی‌توانی به کشور خودت حمله کنی."
        )
        return

    keyboard = [
        [
            InlineKeyboardButton(
                "👥 انتخاب سرباز",
                callback_data=f"attack_soldiers:{target[0]}"
            )
        ],
        [
            InlineKeyboardButton(
                "🚀 انتخاب تجهیزات",
                callback_data=f"attack_items:{target[0]}"
            )
        ],
        [
            InlineKeyboardButton(
                "⚔️ تأیید حمله",
                callback_data=f"attack_confirm:{target[0]}"
            )
        ],
        [
            InlineKeyboardButton(
                "❌ لغو",
                callback_data="close"
            )
        ]
    ]

    await update.message.reply_text(
        f"⚔️ حمله به @{username}\n\n"
        "تعداد سرباز و تجهیزات خودت را انتخاب کن.\n\n"
        "⚠️ این نبرد کاملاً داخل سیستم بازی محاسبه می‌شود.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ==================================================
# پیدا کردن بازیکن
# ==================================================

def find_player_by_username(chat_id, username):

    import sqlite3

    db = sqlite3.connect("war_game.db")
    cursor = db.cursor()

    cursor.execute("""
        SELECT *
        FROM players
        WHERE chat_id = ?
        AND LOWER(username) = ?
    """, (chat_id, username))

    player = cursor.fetchone()

    db.close()

    return player


# ==================================================
# اتحاد
# ==================================================

async def alliance(update: Update, username):

    username = username.replace("@", "")

    keyboard = [
        [
            InlineKeyboardButton(
                "✅ قبول",
                callback_data="alliance_yes"
            ),
            InlineKeyboardButton(
                "❌ رد",
                callback_data="alliance_no"
            )
        ]
    ]

    await update.message.reply_text(
        f"🤝 درخواست اتحاد\n\n"
        f"درخواست اتحاد با @{username}\n\n"
        "اتحاد به معنی صلح دائمی نیست.\n"
        "اعضا همچنان می‌توانند با یکدیگر وارد جنگ شوند.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ==================================================
# داد و ستد
# ==================================================

async def trade(update: Update, username):

    username = username.replace("@", "")

    await update.message.reply_text(
        f"💱 داد و ستد با @{username}\n\n"
        "سیستم پیشنهاد معامله در مرحله بعد اضافه می‌شود."
    )


# ==================================================
# چالش
# ==================================================

async def challenge(update: Update):

    events = [

        (
            "🚨 بحران داخلی!",
            "برای کنترل بحران 5000 پوینت وار پرداخت کن."
        ),

        (
            "🦠 ویروس!",
            "برای ساخت واکسن 12000 پوینت وار پرداخت کن."
        ),

        (
            "📈 رونق اقتصادی!",
            "5000 پوینت وار جایزه گرفتی."
        ),

        (
            "💰 فرصت تجاری!",
            "3000 تا 8000 پوینت وار دریافت کردی."
        )
    ]

    title, description = random.choice(events)

    await update.message.reply_text(
        f"{title}\n\n{description}"
    )


# ==================================================
# مدیریت دکمه‌ها
# ==================================================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    user = query.from_user
    chat_id = query.message.chat.id

    player = get_player(user.id, chat_id)

    if not player:
        await query.message.reply_text(
            "❌ اول بازی را شروع کن."
        )
        return

    data = query.data

    # بستن منو
    if data == "close":

        await query.message.delete()
        return

    # خرید سرباز
    if data.startswith("soldier:"):

        amount = int(data.split(":")[1])

        if amount > 10000:
            return

        price = (amount // 100) * SOLDIER_PRICE

        if player[4] < price:

            await query.message.reply_text(
                "❌ پوینت وار کافی نیست."
            )
            return

        update_player(
            user.id,
            chat_id,
            "points",
            player[4] - price
        )

        update_player(
            user.id,
            chat_id,
            "soldiers",
            player[5] + amount
        )

        await query.message.reply_text(
            f"✅ {amount:,} سرباز خریداری شد!\n\n"
            f"💰 هزینه: {price:,}\n"
            f"👥 سرباز فعلی: {player[5] + amount:,}"
        )

    # خرید موشک
    elif data.startswith("missile:"):

        missile = data.split(":", 1)[1]

        if missile not in MISSILES:
            return

        price = MISSILES[missile]

        if player[4] < price:

            await query.message.reply_text(
                "❌ موجودی پوینت وار کافی نیست."
            )
            return

        update_player(
            user.id,
            chat_id,
            "points",
            player[4] - price
        )

        await query.message.reply_text(
            f"✅ {missile} خریداری شد!\n\n"
            f"💰 هزینه: {price:,}"
        )

    # قبول اتحاد
    elif data == "alliance_yes":

        await query.message.reply_text(
            "🤝 اتحاد تأیید شد!"
        )

    # رد اتحاد
    elif data == "alliance_no":

        await query.message.reply_text(
            "❌ درخواست اتحاد رد شد."
        )


# ==================================================
# پردازش پیام‌های گروه
# ==================================================

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message:
        return

    text = update.message.text.strip()

    # شروع بازی
    if text == "شروع بازی":

        await create_country(update)
        return

    # وضعیت
    if text == "وضعیت کشور":

        await country_status(update)
        return

    # دریافت پوینت
    if text in ["دریافت پوینت", "پوینت وار"]:

        await collect_points(update)
        return

    # خرید موشک
    if text == "خرید موشک":

        await missile_shop(update)
        return

    # خرید سرباز
    if text == "خرید سرباز":

        await soldier_shop(update)
        return

    # خرید قلمرو بدون مقدار
    if text == "خرید قلمرو":

        await territory_shop(update)
        return

    # خرید قلمرو با مقدار
    territory_match = re.match(
        r"^خرید قلمرو\s+(\d+)$",
        text
    )

    if territory_match:

        amount = int(territory_match.group(1))

        await buy_territory(update, amount)
        return

    # حمله
    if text.startswith("حمله ") or text.startswith("حمله@"):

        username = text[5:].strip()

        await attack(update, username)
        return

    # اتحاد
    if text.startswith("اتحاد ") or text.startswith("اتحاد@"):

        username = text[4:].strip()

        await alliance(update, username)
        return

    # داد و ستد
    if text.startswith("داد و ستد ") or text.startswith("دادوستد "):

        username = text.split(" ", 2)[-1]

        await trade(update, username)
        return

    # چالش
    if text == "چالش":

        await challenge(update)
        return

    # سایر پیام‌ها هیچ پاسخی ندارند


# ==================================================
# اجرای ربات
# ==================================================

def main():

    create_database()

    app = Application.builder().token(BOT_TOKEN).build()

    # دستورات اسلشی
    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CommandHandler("help", help_command)
    )

    # دکمه‌ها
    app.add_handler(
        CallbackQueryHandler(button_handler)
    )

    # پیام‌های فارسی
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            text_handler
        )
    )

    print("🌍 WarEmpire is running...")

    app.run_polling()


if __name__ == "__main__":
    main()