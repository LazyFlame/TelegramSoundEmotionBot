import aiosqlite

DB_NAME = "quiz_results.db"


async def init_db():
    """Создает таблицы в базе данных при запуске бота, если их еще нет."""

    async with aiosqlite.connect(DB_NAME) as db:

        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                sound_id TEXT,
                scale_anxiety INTEGER,  -- Тревога (1-5)
                scale_action INTEGER,   -- Побуждение к действию (1-5)
                scale_irritation INTEGER, -- Раздражение (1-5)
                answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        await db.commit()

async def add_user(user_id: int, username: str, first_name: str):
    """Регистрирует нового пользователя."""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, "
            "username,first_name) VALUES (?, ?, ?)",
            (user_id, username, first_name)
        )
        await db.commit()

async def save_answer(user_id: int, sound_id: str,
                      scale_anxiety: int, scale_action: int,
                      scale_irritation: int):
    """Сохраняет все оценки за один раз в конце опроса по конкретному звуку."""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """INSERT INTO answers (user_id, sound_id,
            scale_anxiety, scale_action, scale_irritation)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, sound_id, scale_anxiety, scale_action, scale_irritation)
        )
        await db.commit()
