from aiogram.fsm.state import State, StatesGroup
import random

SOUNDS_DICT = {
    "Test sound.mp3": "CQACAgIAAyEFAATuUsLvAAM_avXYiTDG3diEpm17ife-PiOKxZMAAluwAALQmKlLovBMf9hvRYQ9BA",

    # Аварийные
    "MW.mp3": "CQACAgIAAyEFAATuUsLvAAM5avXX8IL1S_KZksk4rNQTbuxx9TAAAkewAALQmKlLb5leZ7WD48c9BA",
    "SFT.mp3": "CQACAgIAAyEFAATuUsLvAAM-avXYiWhyz2lLPQJJmhxS0CVkxj8AAl2wAALQmKlLNAi9qpq-r5Y9BA",
    "CW.mp3": "CQACAgIAAyEFAATuUsLvAAMxavXXKi_SyQ0v2NLFSovcWD957LEAAjCwAALQmKlLCVgsNdwodTY9BA",
    "AG.mp3": "CQACAgIAAyEFAATuUsLvAAMvavXWt104hg-hOHUHBm6pVXp4K8wAAiSwAALQmKlLLNGrX438h389BA",
    "WD.mp3": "CQACAgIAAyEFAATuUsLvAANAavXYieGiJocAAb3w44YGLPXTwKmUAAJcsAAC0JipSzVqjdta0p7bPQQ",
    "OH.mp3": "CQACAgIAAyEFAATuUsLvAAM6avXYP7CPG3QtD7gmyGXwebX_W68AAlSwAALQmKlLcUVSFitcDfY9BA",

    # Предупреждающие
    "RD.mp3": "CQACAgIAAyEFAATuUsLvAAM7avXYP9QrlS7wdOMyCoHh1cmjTycAAlWwAALQmKlLWOGe3Hd7SJ89BA",
    "MPP.mp3": "CQACAgIAAyEFAATuUsLvAAM4avXX8JTcaA7K-QTSpG72ijAkywkAAkmwAALQmKlLMA_-Urrdqgs9BA",
    "IR.mp3": "CQACAgIAAyEFAATuUsLvAAM1avXXgaDftaOtYlCm_R2bgazFKPUAAj6wAALQmKlLlOIZhv1CI5s9BA",
    "ANLC.mp3": "CQACAgIAAyEFAATuUsLvAAMwavXXKqImJmjnQQABSrlD5kCXgZpmAAIxsAAC0JipS5ZGrPbxxWirPQQ",
    "WSGA.mp3": "CQACAgIAAyEFAATuUsLvAANCavXYtEuNzdgJyjS_2gypNqfdJ8IAAmCwAALQmKlL2v-FDqlswJI9BA",
    "WS.mp3": "CQACAgIAAyEFAATuUsLvAANBavXYtNaxgitqXqveBtwgtW2ImRsAAmGwAALQmKlLZRawt-UmT_Y9BA",
    "SBPL.mp3": "CQACAgIAAyEFAATuUsLvAAM9avXYP96P8rfh25kzvsXbYdPM5qMAAlOwAALQmKlLe6zZpbMZLIM9BA",

    # Уведомительные
    "SB.mp3": "CQACAgIAAyEFAATuUsLvAAM8avXYP4OBsXVw3tMDaDhvLs8xg-oAAlKwAALQmKlLIJwJmuK5e1c9BA",
    "LAR.mp3": "CQACAgIAAyEFAATuUsLvAAM2avXX8NGosNJwFD2mVx_faWdWFGUAAkawAALQmKlLsY7QqgYx_ps9BA",
    "AAA.mp3": "CQACAgIAAyEFAATuUsLvAAMuavXWt4xkPaFz3f8LQbs_5_-sAAGqAAIlsAAC0JipS3_8epHIi7iVPQQ",
    "HN.mp3": "CQACAgIAAyEFAATuUsLvAAM0avXXgczky2mHeiiy0h64IWvvBzQAAj2wAALQmKlLoxMmG1ZAr889BA",
    "GWR.mp3": "CQACAgIAAyEFAATuUsLvAAMzavXXgWTVzz6al0_OhEBsHNrsFy4AAjuwAALQmKlL0RGLt5Eb3Io9BA",
    "GWL.mp3": "CQACAgIAAyEFAATuUsLvAAMyavXXKrJeVxxiYUmL9CMxATSTA_MAAjKwAALQmKlLNEzJe70-JjI9BA",
    "LG.mp3": "CQACAgIAAyEFAATuUsLvAAM3avXX8IqlLPLLPt8wy8qJjv8OjgsAAkiwAALQmKlLusIXNKOk0FA9BA",
}
# Категории для контроля последовательности
CATEGORIES = {
    "emergency": ["MW.mp3", "SFT.mp3", "CW.mp3", "AG.mp3", "WD.mp3", "OH.mp3"],
    "warning": ["RD.mp3", "MPP.mp3", "IR.mp3", "ANLC.mp3", "WSGA.mp3", "WS.mp3", "SBPL.mp3"],
    "informative": ["SB.mp3", "LAR.mp3", "AAA.mp3", "HN.mp3", "GWR.mp3", "GWL.mp3", "LG.mp3"]
}

# 1. Фиксированный список всех 20 звуков
ALL_SOUNDS = (
    CATEGORIES["emergency"] +
    CATEGORIES["warning"] +
    CATEGORIES["informative"]
)

# Словарь для быстрого определения категории звука
SOUND_TO_CAT = {}
for cat, items in CATEGORIES.items():
    for item in items:
        SOUND_TO_CAT[item] = cat


def get_balanced_latin_square_row(participant_index: int, items: list) -> list:
    """
    Возвращает строку сбалансированного латинского квадрата для участника
    с порядковым номером participant_index (0, 1, 2, ...).
    """
    n = len(items)
    row_idx = participant_index % n
    indices = []

    for col in range(n):
        if col % 2 == 0:
            val = (row_idx + col // 2) % n
        else:
            val = (row_idx - (col + 1) // 2) % n
        indices.append(val)

    # Для нечётного числа стимулов квадрат инвертируется во второй половине цикла
    if n % 2 != 0 and (participant_index // n) % 2 == 1:
        indices.reverse()

    return [items[i] for i in indices]


def fix_consecutive_categories(playlist: list) -> list:
    """
    Гарантирует, что в списке нет 3 и более звуков одной категории подряд.
    Если находит нарушение — меняет проблемный звук с ближайшим подходящим.
    """
    res = playlist[:]
    n = len(res)

    for i in range(2, n):
        cat_curr = SOUND_TO_CAT[res[i]]
        cat_prev1 = SOUND_TO_CAT[res[i - 1]]
        cat_prev2 = SOUND_TO_CAT[res[i - 2]]

        if cat_curr == cat_prev1 == cat_prev2:
            # Ищем ближайший звук другой категории дальше по списку
            swapped = False
            for j in range(i + 1, n):
                if SOUND_TO_CAT[res[j]] != cat_curr:
                    res[i], res[j] = res[j], res[i]
                    swapped = True
                    break

            # Если в конце списка не осталось других категорий, меняем с элементом в начале
            if not swapped:
                for j in range(0, i - 2):
                    if SOUND_TO_CAT[res[j]] != cat_curr:
                        # Проверяем, не создаст ли обмен тройку в начале списка
                        temp = res[:]
                        temp[i], temp[j] = temp[j], temp[i]
                        if not _has_three_in_a_row(temp[:i]):
                            res = temp
                            break
    return res


def _has_three_in_a_row(seq: list) -> bool:
    for k in range(2, len(seq)):
        if SOUND_TO_CAT[seq[k]] == SOUND_TO_CAT[seq[k - 1]] == SOUND_TO_CAT[seq[k - 2]]:
            return True
    return False


def generate_latin_playlist(participant_number: int) -> list:
    """
    Главная функция: создаёт последовательность по латинскому квадрату
    с защитой от 3+ звуков одной категории подряд.

    :param participant_number: порядковый номер участника (например, ID записи в БД: 1, 2, 3...)
    """
    # Перемешиваем базовый порядок один раз с фиксированным seed,
    # чтобы категории не шли блоками (6 em, 7 warn, 7 info) в нулевой строке
    base_items = ALL_SOUNDS[:]
    rng = random.Random(42)
    rng.shuffle(base_items)

    raw_playlist = get_balanced_latin_square_row(participant_number, base_items)
    return fix_consecutive_categories(raw_playlist)

# Готовый сбалансированный список для конкретного пользователя (можно вызывать при старте теста)
# SOUNDS_LIST = generate_balanced_playlist()

class QuizStates(StatesGroup):
    waiting_for_consent = State()
    survey_age = State()
    survey_gender = State()
    survey_hearing = State()
    survey_sleep = State()
    survey_aviation = State()
    survey_english = State()
    state_mood = State()
    state_tension = State()
    state_energy = State()
    waiting_for_test_sound = State()
    waiting_to_begin_test = State()
    answering_anxiety = State()
    answering_action = State()
    answering_impulse = State()
    answering_irritation = State()
    answering_valence = State()
    answering_arousal = State()
