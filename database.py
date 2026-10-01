import sqlite3


# ==================================================
# تنظیمات دیتابیس
# ==================================================

DB_NAME = "war_game.db"


# ==================================================
# اتصال به دیتابیس
# ==================================================

def connect():
    return sqlite3.connect(DB_NAME)


# ==================================================
# ساخت دیتابیس
# ==================================================

def create_database():

    db = connect()
    cursor = db.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS players (
            user_id INTEGER,
            chat_id INTEGER,

            username TEXT,
            country TEXT,

            points INTEGER DEFAULT 10000,
            soldiers INTEGER DEFAULT 1000,
            territory INTEGER DEFAULT 10,

            level INTEGER DEFAULT 1,

            attacks INTEGER DEFAULT 0,
            successful_attacks INTEGER DEFAULT 0,
            failed_attacks INTEGER DEFAULT 0,

            successful_defenses INTEGER DEFAULT 0,
            failed_defenses INTEGER DEFAULT 0,

            losses INTEGER DEFAULT 0,

            last_income INTEGER DEFAULT 0,

            PRIMARY KEY (user_id, chat_id)
        )
    """)

    db.commit()
    db.close()


# ==================================================
# پیدا کردن بازیکن
# ==================================================

def get_player(user_id, chat_id):

    db = connect()
    cursor = db.cursor()

    cursor.execute("""
        SELECT *
        FROM players
        WHERE user_id = ?
        AND chat_id = ?
    """, (user_id, chat_id))

    player = cursor.fetchone()

    db.close()

    return player


# ==================================================
# ساخت بازیکن
# ==================================================

def create_player(
    user_id,
    chat_id,
    username,
    points=10000,
    soldiers=1000,
    territory=10
):

    db = connect()
    cursor = db.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO players
        (
            user_id,
            chat_id,
            username,
            country,
            points,
            soldiers,
            territory
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        chat_id,
        username,
        username,
        points,
        soldiers,
        territory
    ))

    db.commit()
    db.close()


# ==================================================
# تغییر اطلاعات بازیکن
# ==================================================

def update_player(
    user_id,
    chat_id,
    column,
    value
):

    allowed_columns = {
        "username",
        "country",
        "points",
        "soldiers",
        "territory",
        "level",
        "attacks",
        "successful_attacks",
        "failed_attacks",
        "successful_defenses",
        "failed_defenses",
        "losses",
        "last_income"
    }

    # جلوگیری از تغییر ستون‌های غیرمجاز
    if column not in allowed_columns:
        raise ValueError(
            f"ستون نامعتبر: {column}"
        )

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        f"""
        UPDATE players
        SET {column} = ?
        WHERE user_id = ?
        AND chat_id = ?
        """,
        (
            value,
            user_id,
            chat_id
        )
    )

    db.commit()
    db.close()


# ==================================================
# تغییر چند اطلاعات همزمان
# ==================================================

def update_player_multiple(
    user_id,
    chat_id,
    **values
):

    allowed_columns = {
        "username",
        "country",
        "points",
        "soldiers",
        "territory",
        "level",
        "attacks",
        "successful_attacks",
        "failed_attacks",
        "successful_defenses",
        "failed_defenses",
        "losses",
        "last_income"
    }

    for column in values:

        if column not in allowed_columns:
            raise ValueError(
                f"ستون نامعتبر: {column}"
            )

    if not values:
        return

    db = connect()
    cursor = db.cursor()

    set_parts = []
    parameters = []

    for column, value in values.items():

        set_parts.append(
            f"{column} = ?"
        )

        parameters.append(value)

    parameters.extend([
        user_id,
        chat_id
    ])

    query = f"""
        UPDATE players
        SET {", ".join(set_parts)}
        WHERE user_id = ?
        AND chat_id = ?
    """

    cursor.execute(
        query,
        parameters
    )

    db.commit()
    db.close()


# ==================================================
# پیدا کردن بازیکن با نام کاربری
# ==================================================

def find_player_by_username(
    chat_id,
    username
):

    username = username.replace("@", "").lower()

    db = connect()
    cursor = db.cursor()

    cursor.execute("""
        SELECT *
        FROM players
        WHERE chat_id = ?
        AND LOWER(username) = ?
    """, (
        chat_id,
        username
    ))

    player = cursor.fetchone()

    db.close()

    return player


# ==================================================
# گرفتن تمام بازیکنان یک گروه
# ==================================================

def get_group_players(chat_id):

    db = connect()
    cursor = db.cursor()

    cursor.execute("""
        SELECT *
        FROM players
        WHERE chat_id = ?
    """, (chat_id,))

    players = cursor.fetchall()

    db.close()

    return players