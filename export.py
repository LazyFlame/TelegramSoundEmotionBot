import sqlite3
import pandas as pd

DB_NAME = "quiz_results.db"
OUTPUT_FILE = "исследование_результаты.xlsx"

def export_to_excel():
    try:
        conn = sqlite3.connect(DB_NAME)

        query = """
        SELECT
            u.user_id AS [Telegram ID],
            u.first_name AS [Имя респондента],
            u.username AS [Юзернейм],
            u.age AS [Возраст],
            u.gender AS [Пол],
            u.hearing_issues AS [Проблемы со слухом],
            u.sleep_quality AS [Качество сна (1-5)],
            u.aviation_experience AS [Опыт пилотирования],
            u.english_level AS [Уровень английского],
            u.state_mood AS [Входное Настроение (1-5)],
            u.state_tension AS [Входная Напряженность (1-5)],
            u.state_energy AS [Входная Энергичность (1-5)],
            u.registered_at AS [Дата регистрации],
            a.sound_id AS [Аудиостимул],
            a.scale_anxiety AS [Шкала Тревоги (1-5)],
            a.scale_action AS [Шкала Действия (1-5)],
            a.scale_impulse AS [Шкала Импульса (1-5)],
            a.scale_irritation AS [Шкала Раздражения (1-5)],
            a.scale_valence AS [Шкала Валентности (1-5)],
            a.scale_arousal AS [Шкала Возбуждения (1-5)],
            a.answered_at AS [Время ответа]
        FROM answers a
        JOIN users u ON a.user_id = u.user_id
        ORDER BY a.answered_at ASC
        """

        df = pd.read_sql_query(query, conn)

        if df.empty:
            print("⚠️ База данных пока пуста. Респонденты еще не прошли тест.")
            conn.close()
            return

        df.to_excel(OUTPUT_FILE, index=False, sheet_name="Результаты теста")
        print(f"✅ Данные успешно выгружены в файл: {OUTPUT_FILE}")

        conn.close()

    except sqlite3.OperationalError as e:
        print(f"Ошибка базы данных: {e}")
    except Exception as e:
        print(f"Произошла ошибка при экспорте: {e}")

if __name__ == "__main__":
    export_to_excel()
