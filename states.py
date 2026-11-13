from aiogram.fsm.state import State, StatesGroup

class QuizStates(StatesGroup):
    # Блок анкетирования
    waiting_for_agreement = State()
    waiting_for_age = State()
    waiting_for_gender = State()
    waiting_for_hearing = State()
    waiting_for_sleep = State()
    waiting_for_piloting = State()
    waiting_for_english = State()
    waiting_for_headphones = State()

    # Входное состояние (3 вопроса)
    waiting_for_mood = State()
    waiting_for_tension = State()
    waiting_for_energy = State()

    # Калибровка звука
    waiting_for_volume_check = State()

    # Оценка звуков
    waiting_for_scale_answer = State()
