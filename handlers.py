import os
from aiogram import Router, F, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from quiz import QuizStates, SOUNDS_DICT, generate_balanced_playlist
import database as db

router = Router()

def get_scale_keyboard():
    """Клавиатура с цифрами 1-5."""
    buttons = [
        [InlineKeyboardButton(text=str(i), callback_data=f"score_{i}") for i in range(1, 6)]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    """Старт, проверка незавершённой сессии или запуск анкетирования."""
    user_id = message.from_user.id

    # Проверяем, есть ли уже данные по этому пользователю в БД
    playlist, answered_sounds = await db.get_user_progress(user_id)

    if playlist:
        # Пользователь уже существует в базе
        answered_count = len(answered_sounds)
        total_sounds = len(playlist)

        if answered_count >= total_sounds:
            # Тест уже полностью пройден
            await message.answer("Вы уже успешно завершили всё тестирование. Большое спасибо за участие!")
            return

        # Есть незавершённый прогресс — предлагаем продолжить
        await state.clear()

        # Восстанавливаем плейлист и индекс в память FSM
        await state.update_data(
            user_playlist=playlist,
            current_sound_index=answered_count
        )

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Продолжить тестирование", callback_data="resume_test")],
            [InlineKeyboardButton(text="Начать сначала", callback_data="restart_test")]
        ])

        await message.answer(
            f"У вас есть незавершённая сессия тестирования!\n\n"
            f"Пройдено звуков: <b>{answered_count} из {total_sounds}</b>.\n\n"
            "Хотите продолжить с прерванного места или начать сначала?",
            reply_markup=kb,
            parse_mode="HTML"
        )
        return

    # Если пользователя в базе нет — стандартный старт с согласия
    await state.clear()

    text = (
        f"Здравствуйте! 👋\n"
        "Добро пожаловать в психологическое исследование восприятия звуковых стимулов кабины воздушного судна.\n\n"
        "<b>Условия участия:</b>\n"
        "🔹 Исследование полностью анонимно.\n"
        "🔹 Длительность: 10–15 минут.\n"
        "🔹 Тест можно прервать в любой момент и продолжить позже с того же места.\n"
        "🔹 Участие добровольное.\n\n"
        "Нажимая кнопку «Согласен(на)», вы подтверждаете своё согласие на участие."
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Согласен(на)", callback_data="consent_yes")],
        [InlineKeyboardButton(text="Не согласен(на)", callback_data="consent_no")]
    ])

    await message.answer(text, reply_markup=kb, parse_mode="HTML")
    await state.set_state(QuizStates.waiting_for_consent)


@router.callback_query(F.data == "resume_test")
async def resume_test_process(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.delete()
    # Запускаем отправку следующего звука с сохраненного индекса
    await send_next_sound_stimulus(callback.message, state)


@router.callback_query(F.data == "restart_test")
async def restart_test_process(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.delete()

    # Можно при желании очистить старые ответы из базы для этого юзера или просто начать заново:
    text = (
        f"Здравствуйте! 👋\n"
        "Добро пожаловать в психологическое исследование восприятия звуковых стимулов кабины воздушного судна.\n\n"
        "Нажимая кнопку «Согласен(на)», вы подтверждаете своё согласие на участие."
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Согласен(на)", callback_data="consent_yes")],
        [InlineKeyboardButton(text="Не согласен(на)", callback_data="consent_no")]
    ])
    await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
    await state.set_state(QuizStates.waiting_for_consent)


@router.callback_query(QuizStates.waiting_for_consent, F.data == "consent_no")
async def consent_refused(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_text("Вы отказались от участия в исследовании. Спасибо за уделённое время!")
    await state.clear()


@router.callback_query(QuizStates.waiting_for_consent, F.data == "consent_yes")
async def consent_accepted(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_text("Спасибо! Начнем с небольшой анкеты.\n\nПожалуйста, введите ваш возраст:")
    await state.set_state(QuizStates.survey_age)


@router.message(QuizStates.survey_age)
async def process_age(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введите возраст числом (например, 25):")
        return

    age = int(message.text)
    if not (16 <= age <= 99):
        await message.answer("К сожалению, введен некорректный возраст. Попробуйте еще раз:")
        return

    await state.update_data(age=age)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Мужской", callback_data="gender_m"), InlineKeyboardButton(text="Женский", callback_data="gender_f")]
    ])
    await message.answer("Укажите ваш пол:", reply_markup=kb)
    await state.set_state(QuizStates.survey_gender)


@router.callback_query(QuizStates.survey_gender, F.data.startswith("gender_"))
async def process_gender(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    gender = "Мужской" if callback.data == "gender_m" else "Женский"
    await state.update_data(gender=gender)

    text = (
        "<b>Есть ли у вас сейчас заложенность ушей или проблемы со слухом?</b>\n\n"
        "🔹 <b>Нет, слух в норме</b> — слышу хорошо, дискомфорта нет.\n"
        "🔹 <b>Есть лёгкие отклонения</b> — небольшая заложенность или незначительное снижение слуха.\n"
        "🔹 <b>Есть выраженные нарушения</b> — серьёзное снижение слуха или сильная заложенность."
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Нет, слух в норме", callback_data="hearing_no")],
        [InlineKeyboardButton(text="Есть лёгкая заложенность", callback_data="hearing_unsure")],
        [InlineKeyboardButton(text="Да, есть выраженные нарушения слуха", callback_data="hearing_yes")],
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await state.set_state(QuizStates.survey_hearing)


@router.callback_query(QuizStates.survey_hearing, F.data.startswith("hearing_"))
async def process_hearing(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    mapping = {"hearing_no": "нет", "hearing_yes": "да", "hearing_unsure": "не уверен"}
    await state.update_data(hearing_issues=mapping[callback.data])

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=str(i), callback_data=f"sleep_{i}") for i in range(1, 6)]
    ])
    await callback.message.edit_text(
        "Хорошо ли вы сегодня спали?\n\n(1 — спал мало, 3 — средне, 5 — хорошо выспался)",
        reply_markup=kb
    )
    await state.set_state(QuizStates.survey_sleep)


@router.callback_query(QuizStates.survey_sleep, F.data.startswith("sleep_"))
async def process_sleep(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    sleep_score = int(callback.data.split("_")[1])
    await state.update_data(sleep_quality=sleep_score)

    text = (
        "Насколько хорошо вы знакомы с бортовыми системами оповещения и звуками кабины самолёта?\n\n"
        "🔹 <b>Совсем не знаком</b> — опыт только в роли пассажира.\n\n"
        "🔹 <b>Поверхностно знаком</b> — слышал сигналы в фильмах, играх или видеороликах.\n\n"
        "🔹 <b>Знаком как любитель</b> — увлекаюсь авиацией, играю в авиасимуляторы.\n\n"
        "🔹 <b>Есть практический / учебный опыт</b> — изучал системы в ВУЗе, был на тренажёрах или в кабине."
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Совсем не знаком", callback_data="av_no")],
        [InlineKeyboardButton(text="Поверхностно знаком", callback_data="av_sup")],
        [InlineKeyboardButton(text="Знаком как любитель", callback_data="av_ama")],
        [InlineKeyboardButton(text="Имею практический или учебный опыт", callback_data="av_prof")],
    ])

    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await state.set_state(QuizStates.survey_aviation)


@router.callback_query(QuizStates.survey_aviation, F.data.startswith("av_"))
async def process_aviation(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    mapping = {
        "av_no": "Совсем не знаком",
        "av_sup": "Поверхностно знаком",
        "av_ama": "Знаком как любитель",
        "av_prof": "Практический / учебный опыт"
    }
    await state.update_data(aviation_experience=mapping[callback.data])

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Нет", callback_data="eng_no")],
        [InlineKeyboardButton(text="A1–A2", callback_data="eng_a1")],
        [InlineKeyboardButton(text="B1", callback_data="eng_b1")],
        [InlineKeyboardButton(text="B2–C2", callback_data="eng_b2")]
    ])

    english_prompt = (
        "Знаете ли вы английский язык?\n\n"
        "• <b>Нет</b>\n"
        "• <b>A1–A2</b> — понимаю отдельные слова\n"
        "• <b>B1</b> — понимаю общий смысл\n"
        "• <b>B2–C2</b> — свободно воспринимаю на слух"
    )

    await callback.message.edit_text(english_prompt, reply_markup=kb, parse_mode="HTML")
    await state.set_state(QuizStates.survey_english)


@router.callback_query(QuizStates.survey_english, F.data.startswith("eng_"))
async def process_english(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    mapping = {
        "eng_no": "Нет",
        "eng_a1": "A1–A2",
        "eng_b1": "B1",
        "eng_b2": "B2–C2"
    }
    await state.update_data(english_level=mapping[callback.data])

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=str(i), callback_data=f"mood_{i}") for i in range(1, 6)]
    ])
    await callback.message.edit_text(
        "Как вы оцениваете своё настроение в данный момент?\n\n(1 — подавленное, 3 — нейтральное, 5 — отличное)",
        reply_markup=kb
    )
    await state.set_state(QuizStates.state_mood)


@router.callback_query(QuizStates.state_mood, F.data.startswith("mood_"))
async def process_state_mood(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    mood = int(callback.data.split("_")[1])
    await state.update_data(state_mood=mood)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=str(i), callback_data=f"tension_{i}") for i in range(1, 6)]
    ])
    await callback.message.edit_text(
        "Чувствуете ли вы сейчас внутреннее напряжение или тревогу?\n\n(1 — полностью спокоен, 3 — лёгкое напряжение, 5 — сильно напряжён)",
        reply_markup=kb
    )
    await state.set_state(QuizStates.state_tension)


@router.callback_query(QuizStates.state_tension, F.data.startswith("tension_"))
async def process_state_tension(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    tension = int(callback.data.split("_")[1])
    await state.update_data(state_tension=tension)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=str(i), callback_data=f"energy_{i}") for i in range(1, 6)]
    ])
    await callback.message.edit_text(
        "Насколько бодрым и отдохнувшим вы чувствуете себя прямо сейчас?\n\n(1 — сильно уставший, 3 — нейтральное состояние, 5 — полон сил)",
        reply_markup=kb
    )
    await state.set_state(QuizStates.state_energy)


@router.callback_query(QuizStates.state_energy, F.data.startswith("energy_"))
async def process_state_energy(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    energy = int(callback.data.split("_")[1])
    await state.update_data(state_energy=energy)

    data = await state.get_data()
    user = callback.from_user
    await db.save_user_profile(user.id, user.username, user.first_name, data)

    ready_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Готов продолжить", callback_data="start_main_test")]
    ])
    volume_text = (
        "🔊 <b>Настройка громкости</b>\n\n"
        "🔹 Пожалуйста, обязательно наденьте наушники.\n"
        "🔹 По возможности найдите тихое, спокойное место.\n"
        "🔹 Прослушайте тестовый сигнал ниже.\n"
        "🔹 Установите комфортную громкость."
    )

    await callback.message.edit_text(text=volume_text, reply_markup=ready_kb, parse_mode="HTML")

    try:
        test_file_id = SOUNDS_DICT["Test sound.mp3"]
        sent_test_msg = await callback.message.answer_document(document=test_file_id, caption="Тестовый сигнал")
        await state.update_data(test_audio_msg_id=sent_test_msg.message_id)
    except Exception as e:
        print(f"Ошибка отправки тест-звука: {e}")

    await state.set_state(QuizStates.waiting_for_test_sound)


@router.callback_query(QuizStates.waiting_for_test_sound, F.data == "start_main_test")
async def start_main_test(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()

    # Пытаемся удалить сообщение с тестовым звуком, если его ID сохранился в состоянии
    data = await state.get_data()
    test_audio_msg_id = data.get("test_audio_msg_id")
    if test_audio_msg_id:
        try:
            await callback.bot.delete_message(chat_id=callback.message.chat.id, message_id=test_audio_msg_id)
        except Exception:
            pass

    instruction_text = (
        "🎧 <b>Отлично, всё готово к началу!</b>\n\n"
        "Вас ждут <b>20 коротких звуковых сигналов</b>.\n"
        "После каждого звука нужно ответить на <b>6 вопросов</b> (оценки от 1 до 5).\n\n"
        "💡 <i>Слушайте сигнал полностью, опирайтесь на первые ощущения. Правильных или неправильных ответов нет.</i>"
    )

    ready_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Приступить к оценке", callback_data="begin_first_sound")]
    ])

    await callback.message.edit_text(instruction_text, reply_markup=ready_kb, parse_mode="HTML")
    await state.set_state(QuizStates.waiting_to_begin_test)


@router.callback_query(QuizStates.waiting_to_begin_test, F.data == "begin_first_sound")
async def begin_first_sound(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()

    user_playlist = generate_balanced_playlist()
    await state.update_data(current_sound_index=0, user_playlist=user_playlist)
    await callback.message.delete()

    await send_next_sound_stimulus(callback.message, state)


async def send_next_sound_stimulus(message: types.Message, state: FSMContext):
    data = await state.get_data()
    idx = data["current_sound_index"]
    user_playlist = data["user_playlist"]

    if idx >= len(user_playlist):
        # Удаляем последнее аудио перед финалом, если оно осталось
        old_audio_msg_id = data.get("last_audio_msg_id")
        if old_audio_msg_id:
            try:
                await message.bot.delete_message(chat_id=message.chat.id, message_id=old_audio_msg_id)
            except Exception:
                pass

        await message.answer("Большое спасибо! Вы успешно завершили первую часть исследования. Ваши данные сохранены.")
        await state.clear()
        return

    # 1. Удаляем предыдущее аудиосообщение, если оно было
    old_audio_msg_id = data.get("last_audio_msg_id")
    if old_audio_msg_id:
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=old_audio_msg_id)
        except Exception:
            pass  # Если сообщение уже удалено, игнорируем ошибку

    sound_key = user_playlist[idx]
    file_id = SOUNDS_DICT[sound_key]

    # Информируем о номере стимула
    await message.answer(f"🎧 <b>Стимул №{idx + 1} из {len(user_playlist)}</b>", parse_mode="HTML")

    try:
        # 2. Отправляем новый файл и сохраняем его message_id
        sent_msg = await message.answer_document(document=file_id)
        await state.update_data(last_audio_msg_id=sent_msg.message_id)
    except Exception as e:
        print(f"Не удалось отправить документ {sound_key}: {e}")

    # Задаем первый вопрос по шкалам
    msg = await message.answer(
        "Насколько этот звук вызывает у вас тревогу?\n\n(1 — совсем не вызывает, 5 — вызывает сильную тревогу)",
        reply_markup=get_scale_keyboard()
    )

    await state.update_data(current_message_id=msg.message_id, sound_id=sound_key)
    await state.set_state(QuizStates.answering_anxiety)


# --- ЦЕПОЧКА ИЗ 6 ШКАЛ ---

@router.callback_query(QuizStates.answering_anxiety, F.data.startswith("score_"))
async def handle_anxiety(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    score = int(callback.data.split("_")[1])
    await state.update_data(anxiety=score)

    await callback.message.edit_text(
        "Насколько этот звук побуждает вас к действию?\n\n(1 — не побуждает, его можно не замечать, 5 — требует немедленно отреагировать)",
        reply_markup=get_scale_keyboard()
    )
    await state.set_state(QuizStates.answering_action)


@router.callback_query(QuizStates.answering_action, F.data.startswith("score_"))
async def handle_action(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    score = int(callback.data.split("_")[1])
    await state.update_data(action=score)

    await callback.message.edit_text(
        "Насколько вам хочется прекратить этот звук?\n\n(1 — совсем не хочется, 5 — очень хочется)",
        reply_markup=get_scale_keyboard()
    )
    await state.set_state(QuizStates.answering_impulse)


@router.callback_query(QuizStates.answering_impulse, F.data.startswith("score_"))
async def handle_impulse(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    score = int(callback.data.split("_")[1])
    await state.update_data(impulse=score)

    await callback.message.edit_text(
        "Насколько этот звук вас раздражает?\n\n(1 — совсем не раздражает, 5 — сильно раздражает)",
        reply_markup=get_scale_keyboard()
    )
    await state.set_state(QuizStates.answering_irritation)


@router.callback_query(QuizStates.answering_irritation, F.data.startswith("score_"))
async def handle_irritation(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    score = int(callback.data.split("_")[1])
    await state.update_data(irritation=score)

    await callback.message.edit_text(
        "Насколько этот звук приятен или неприятен?\n\n(1 — очень неприятен, 3 — нейтрален, 5 — очень приятен)",
        reply_markup=get_scale_keyboard()
    )
    await state.set_state(QuizStates.answering_valence)


@router.callback_query(QuizStates.answering_valence, F.data.startswith("score_"))
async def handle_valence(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    score = int(callback.data.split("_")[1])
    await state.update_data(valence=score)

    await callback.message.edit_text(
        "Насколько этот звук вас взбадривает или успокаивает?\n\n(1 — совершенно спокойный, 5 — звук сильно взбодрил)",
        reply_markup=get_scale_keyboard()
    )
    await state.set_state(QuizStates.answering_arousal)


@router.callback_query(QuizStates.answering_arousal, F.data.startswith("score_"))
async def handle_arousal(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    arousal_score = int(callback.data.split("_")[1])

    data = await state.get_data()
    user_id = callback.from_user.id
    sound_id = data["sound_id"]

    scores = {
        "anxiety": data["anxiety"],
        "action": data["action"],
        "impulse": data["impulse"],
        "irritation": data["irritation"],
        "valence": data["valence"],
        "arousal": arousal_score
    }

    await db.save_answer(user_id, sound_id, scores)

    # Безопасно обновляем текст, игнорируя ошибку, если сообщение не изменилось
    try:
        await callback.message.edit_text("Оценка сохранена ✓")
    except Exception:
        pass

    idx = data["current_sound_index"]
    await state.update_data(current_sound_index=idx + 1)
    await send_next_sound_stimulus(callback.message, state)