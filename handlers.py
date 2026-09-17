#функции-обработчики команд
from aiogram import Router, F, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.types import FSInputFile

from quiz import QuizStates, SOUNDS_LIST
import database as db

router = Router()


def get_scale_keyboard():
    """Создает клавиатуру с цифрами 1-5 (Вариант 1)"""
    buttons = [
        [InlineKeyboardButton(text=str(i),
                              callback_data=f"score_{i}") for i in range(1, 6)]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    """Старт бота, запись пользователя в БД и отправка технического звука."""
    await state.clear()

    await db.add_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name
    )

    await message.answer(
        f"Здравствуйте, {message.from_user.first_name}!\n"
        "Добро пожаловать в психологическое исследование восприятия звуковых стимулов.\n\n"
        "Пожалуйста, наденьте наушники и выставьте комфортную громкость.\n"
        "Сейчас я пришлю проверочный звук, чтобы вы настроили аудио."
    )

    try:
        test_sound = FSInputFile("sounds/test_sound.wav")
        await message.answer_audio(audio=test_sound, caption="Проверьте громкость.")
    except Exception:

        await message.answer("*(Здесь должен быть файл `test_sound.mp3`)*")

    ready_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Всё слышно, готов начать тест",
                              callback_data="start_test")]
    ])
    await message.answer("Как только настроите звук, нажмите кнопку ниже:",
                         reply_markup=ready_kb)
    await state.set_state(QuizStates.waiting_for_test_sound)


@router.callback_query(QuizStates.waiting_for_test_sound,
                       F.data == "start_test")
async def start_quiz(callback: types.CallbackQuery, state: FSMContext):
    """Начало основного теста. Отправка первого звука."""
    await callback.answer()

    await state.update_data(current_sound_index=0)

    await send_next_sound(callback.message, state)


async def send_next_sound(message: types.Message, state: FSMContext):
    """Отправка очередного звука и первого вопроса."""
    data = await state.get_data()
    idx = data["current_sound_index"]

    if idx >= len(SOUNDS_LIST):
        await message.answer("Большое спасибо! Вы успешно прошли исследование.")
        await state.clear()
        return

    sound_name = SOUNDS_LIST[idx]
    await message.answer(f"Стимул №{idx + 1}")

    try:
        audio = FSInputFile(f"sounds/{sound_name}")
        await message.answer_audio(audio=audio)
    except Exception:
        await message.answer(f"(Здесь должен быть файл {sound_name})")

    await message.answer(
        "Вопрос 1 из 3:\n**Насколько этот звук вызывает у вас "
        "чувство тревоги или опасности?**\n"
        "(1 — абсолютно спокоен, 5 — крайняя степень тревоги)",
        reply_markup=get_scale_keyboard()
    )
    await state.set_state(QuizStates.waiting_for_anxiety)


@router.callback_query(QuizStates.waiting_for_anxiety,
                       F.data.startswith("score_"))
async def handle_anxiety(callback: types.CallbackQuery, state: FSMContext):
    """Ловит ответ на 1-й вопрос и задаёт 2-й."""
    await callback.answer()
    score = int(callback.data.split("_")[1])

    await state.update_data(anxiety_score=score)

    await callback.message.edit_text(
        "Вопрос 2 из 3:\n Насколько этот звук побуждает "
        "к немедленному действию?\n"
        "(1 — можно проигнорировать, 5 — требует моментального действия)",
        reply_markup=get_scale_keyboard()
    )
    await state.set_state(QuizStates.waiting_for_action)


@router.callback_query(QuizStates.waiting_for_action, F.data.startswith("score_"))
async def handle_action(callback: types.CallbackQuery, state: FSMContext):
    """Ловим ответ на 2-й вопрос и задаем 3-й."""
    await callback.answer()
    score = int(callback.data.split("_")[1])

    await state.update_data(action_score=score)

    await callback.message.edit_text(
        "Вопрос 3 из 3:\n**Насколько этот звук раздражает или утомляет?**\n"
        "(1 — нейтральный, 5 — крайне неприятный)",
        reply_markup=get_scale_keyboard()
    )
    await state.set_state(QuizStates.waiting_for_irritation)


@router.callback_query(QuizStates.waiting_for_irritation, F.data.startswith("score_"))
async def handle_irritation(callback: types.CallbackQuery, state: FSMContext):
    """Ловит 3-й ответ, записываем всё в БД SQLite и двигаемся к следующему звуку."""
    await callback.answer()
    irritation_score = int(callback.data.split("_")[1])

    data = await state.get_data()
    idx = data["current_sound_index"]
    sound_name = SOUNDS_LIST[idx]
    anxiety_score = data["anxiety_score"]
    action_score = data["action_score"]
    user_id = callback.from_user.id

    print(f"Попытка записи в БД: User {user_id}, Sound {sound_name}, "
          f"Оценки: {anxiety_score}, {action_score}, {irritation_score}")

    await db.save_answer(
        user_id=user_id,
        sound_id=sound_name,
        scale_anxiety=anxiety_score,
        scale_action=action_score,
        scale_irritation=irritation_score
    )

    print("Успешно записано в базу данных!")

    await callback.message.edit_text("Оценка принята. Переходим дальше...")

    await state.update_data(current_sound_index=idx + 1)

    await send_next_sound(callback.message, state)
