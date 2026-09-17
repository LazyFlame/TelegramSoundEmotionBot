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
            u.registered_at AS [Дата регистрации],
            a.sound_id AS [Аудиостимул],
            a.scale_anxiety AS [Шкала тревоги (1-5)],
            a.scale_action AS [Шкала действия (1-5)],
            a.scale_irritation AS [Шкала раздражения (1-5)],
            a.answered_at AS [Время ответа]
        FROM answers a
        JOIN users u ON a.user_id = u.user_id
        ORDER BY a.answered_at ASC
        """

        df = pd.read_sql_query(query, conn)

        if df.empty:
            print(" База данных пуста")
            conn.close()
            return

        df.to_excel(OUTPUT_FILE, index=False, sheet_name="Результаты теста")
        print(f"Данные успешно выгружены в файл: {OUTPUT_FILE}")

        conn.close()

    except sqlite3.OperationalError:
        print("Ошибка: Файл базы данных еще не создан.")
    except Exception as e:
        print(f"Произошла ошибка при экспорте: {e}")

if __name__ == "__main__":
    export_to_excel()
