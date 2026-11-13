from datetime import datetime, timezone
import database as db

# Список из 24 звуков (замени на реальные имена файлов из папки sounds/)
SOUNDS_LIST = [f"S{i:02d}.wav" for i in range(1, 25)]

SCALES_CONFIG = [
    {
        "key": "anxiety",
        "text": "Вопрос 1 из 6:\n\n**Насколько этот звук вызывает у вас тревогу?**\n\n1 — совсем не вызывает\n5 — вызывает сильную тревогу"
    },
    {
        "key": "action",
        "text": "Вопрос 2 из 6:\n\n**Насколько этот звук побуждает вас к действию?**\n\n1 — не побуждает, его можно не замечать\n5 — требует немедленно отреагировать"
    },
    {
        "key": "impulse",
        "text": "Вопрос 3 из 6:\n\n**Насколько вам хочется прекратить этот звук?**\n\n1 — совсем не хочется\n5 — очень хочется"
    },
    {
        "key": "irritation",
        "text": "Вопрос 4 из 6:\n\n**Насколько этот звук вас раздражает?**\n\n1 — совсем не раздражает\n5 — сильно раздражает"
    },
    {
        "key": "valence",
        "text": "Вопрос 5 из 6:\n\n**Насколько этот звук приятен или неприятен?**\n\n1 — очень неприятен\n3 — нейтрален\n5 — очень приятен"
    },
    {
        "key": "arousal",
        "text": "Вопрос 6 из 6:\n\n**Насколько этот звук вас взбадривает или успокаивает?**\n\n1 — совершенно спокойный\n5 — звук сильно взбодрил"
    }
]

async def get_respondent_progress(user_id: int):
    """Возвращает индекс текущего звука, имя файла и номер для отображения."""
    answered_count = await db.get_answered_sounds_count(user_id)

    if answered_count >= len(SOUNDS_LIST):
        return None  # Тест полностью пройден

    return {
        "index": answered_count,
        "filename": SOUNDS_LIST[answered_count],
        "display_number": answered_count + 1,
        "total": len(SOUNDS_LIST)
    }

def calculate_ms_delta(start_iso_str: str) -> int:
    """Вычисляет разницу в миллисекундах между стартом и текущим моментом UTC."""
    start_time = datetime.fromisoformat(start_iso_str)
    now = datetime.now(timezone.utc)
    delta = now - start_time
    return int(delta.total_seconds() * 1000)
