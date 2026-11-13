import aiosqlite

DB_NAME = "quiz_results.db"

async def init_db():
    """Создает таблицы в базе данных при запуске бота, если их еще нет."""
    async with aiosqlite.connect(DB_NAME) as db:
        # Таблица пользователей с плейлистом и временем завершения
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                age INTEGER,
                gender TEXT,
                hearing_issues TEXT,
                sleep_quality INTEGER,
                aviation_experience TEXT,
                english_level TEXT,
                has_headphones TEXT,
                is_quiet_room TEXT,
                state_mood INTEGER,
                state_tension INTEGER,
                state_energy INTEGER,
                playlist TEXT, -- Сохраненный порядок звуков (через запятую)
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
        """)

        # Таблица ответов по звукам
        await db.execute("""
            CREATE TABLE IF NOT EXISTS answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                sound_id TEXT,
                scale_anxiety INTEGER,
                scale_action INTEGER,
                scale_impulse INTEGER,
                scale_irritation INTEGER,
                scale_valence INTEGER,
                scale_arousal INTEGER,
                answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        await db.commit()

async def save_user_profile(user_id: int, username: str, first_name: str, data: dict, playlist_str: str = None):
    """Сохраняет или обновляет анкетные данные респондента вместе с плейлистом."""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            INSERT INTO users (
                user_id, username, first_name, age, gender, hearing_issues,
                sleep_quality, aviation_experience, english_level,
                has_headphones, is_quiet_room, state_mood, state_tension, state_energy, playlist
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                age=excluded.age,
                gender=excluded.gender,
                hearing_issues=excluded.hearing_issues,
                sleep_quality=excluded.sleep_quality,
                aviation_experience=excluded.aviation_experience,
                english_level=excluded.english_level,
                has_headphones=excluded.has_headphones,
                is_quiet_room=excluded.is_quiet_room,
                state_mood=excluded.state_mood,
                state_tension=excluded.state_tension,
                state_energy=excluded.state_energy,
                playlist = COALESCE(users.playlist, excluded.playlist)
            """,
            (
                user_id, username, first_name,
                data.get("age"),
                data.get("gender"),
                data.get("hearing_issues"),
                data.get("sleep_quality"),
                data.get("aviation_experience"),
                data.get("english_level"),
                data.get("has_headphones"),
                data.get("is_quiet_room"),
                data.get("state_mood"),
                data.get("state_tension"),
                data.get("state_energy"),
                playlist_str
            )
        )
        await db.commit()

async def update_user_playlist(user_id: int, playlist_str: str):
    """Сохраняет сгенерированный плейлист для пользователя."""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET playlist = ? WHERE user_id = ?", (playlist_str, user_id))
        await db.commit()

async def get_user_progress(user_id: int):
    """Возвращает информацию о пользователе и список уже пройденных звуков."""
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT playlist, completed_at FROM users WHERE user_id = ?", (user_id,)) as cursor:
            user_row = await cursor.fetchone()

        if not user_row:
            return None, []

        playlist_str, completed_at = user_row
        playlist = playlist_str.split(",") if playlist_str else []

        async with db.execute("SELECT sound_id FROM answers WHERE user_id = ?", (user_id,)) as cursor:
            answered_rows = await cursor.fetchall()
            answered_sounds = [row[0] for row in answered_rows]

        return playlist, answered_sounds


async def get_last_sound_answered_scales_count(user_id: int, sound_id: str) -> int:
    """Возвращает количество ответов на шкалы для конкретного звука пользователя."""
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            """
            SELECT scale_anxiety, scale_action, scale_impulse, scale_irritation, scale_valence, scale_arousal
            FROM answers WHERE user_id = ? AND sound_id = ?
            """,
            (user_id, sound_id)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                return 0
            return sum(1 for val in row if val is not None)


async def mark_test_completed(user_id: int):
    """Отмечает время завершения теста."""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET completed_at = CURRENT_TIMESTAMP WHERE user_id = ?", (user_id,))
        await db.commit()

async def save_answer(user_id: int, sound_id: str, scores: dict):
    """Сохраняет оценки по 6 шкалам для конкретного звука."""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            INSERT INTO answers (
                user_id, sound_id, scale_anxiety, scale_action,
                scale_impulse, scale_irritation, scale_valence, scale_arousal
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id, sound_id,
                scores.get("anxiety"),
                scores.get("action"),
                scores.get("impulse"),
                scores.get("irritation"),
                scores.get("valence"),
                scores.get("arousal")
            )
        )
        await db.commit()
