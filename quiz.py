from aiogram.fsm.state import State, StatesGroup

SOUNDS_LIST = [
    "te_climb.wav",
    "te_descend.wav",
    "transonic.wav",
    "wshr.wav",
]

class QuizStates(StatesGroup):
    """Состояния, в которых может находиться респондент во время теста."""
    waiting_for_test_sound = State()
    waiting_for_anxiety = State()
    waiting_for_action = State()
    waiting_for_irritation = State()
