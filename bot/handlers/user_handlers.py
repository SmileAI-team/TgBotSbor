import asyncio
import logging
from io import BytesIO
from aiogram.types import BufferedInputFile, InputMediaVideo, FSInputFile
from aiogram.types import BufferedInputFile, InputMediaVideo, FSInputFile
from aiogram import Router, types, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from ..keyboards.user_keyboards import *
from ..queue.rabbitmq_client import rpc_call, send_to_save
from .logging_utils import log_event, start_log_scheduler
from datetime import datetime
import base64

# Инициализация логгера
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
router = Router()


user_data = {}


class UploadStates(StatesGroup):
    waiting_for_photos = State()


class FeedbackStates(StatesGroup):
    waiting_for_feedback = State()
    waiting_for_choice = State()


# --------------------- Базовые обработчики ---------------------
@router.message(CommandStart())
async def start(message: types.Message, state: FSMContext):
    """Обработчик старта бота с приветствием и запросом согласия"""
    user_id = message.from_user.id
    await log_event("user_info", "User started bot", user_id)
    logger.info(f"User {user_id} gave consent")

    # Приветственное сообщение
    await message.answer(
        "Добро пожаловать! Этот бот поможет провести диагностику состояния зубов "
        "с использованием фотографий и искусственного интеллекта 🦷"
    )

    privacy_policy_link = "<a href='https://docs.google.com/document/d/1vBwBFJbYjn_jLhNvjALf_auXysNFzPmdh0mE6XV0_YI/edit?usp=sharing'>Пользовательским соглашением</a>"
    await message.answer(
        f"Используя этого бота, вы автоматически соглашаетесь "
        f"на обработку ваших персональных данных, включая фотографии полости рта, "
        f"для целей диагностики и предоставления рекомендаций."
        f"Вы можете ознакомиться с {privacy_policy_link}.",
        # parse_mode="HTML",
        disable_web_page_preview=True
    )
    await asyncio.sleep(2)
    await show_instructions(message)
    await state.clear()


@router.callback_query(FeedbackStates.waiting_for_choice, F.data == "ask_feedback")
async def ask_feedback(call: types.CallbackQuery, state: FSMContext):
    await call.message.edit_reply_markup()  # Убираем кнопки
    await call.message.answer("Напишите ваш отзыв или предложение:", reply_markup=cancel_keyboard)
    await state.set_state(FeedbackStates.waiting_for_feedback)


@router.callback_query(FeedbackStates.waiting_for_choice, F.data == "skip_feedback")
async def skip_feedback(call: types.CallbackQuery, state: FSMContext):
    await log_event("feedback", "User skipped feedback", call.from_user.id)
    await call.message.edit_reply_markup()  # Убираем кнопки
    await call.message.answer("Спасибо за использование нашего сервиса!", reply_markup=main_keyboard)
    await state.clear()


async def show_instructions(message: types.Message):
    """Функция показа инструкции с фото"""
    instructions = (
        "Подготовка перед съемкой\n"
        "✅ Убедитесь, что вы находитесь в ярко освещённом месте.\n"
        "✅ Включите вспышку на телефоне, чтобы AI мог правильно распознать детали.\n"
        "✅ Используйте фронтальную камеру (селфи-камера) для всех фото."
    )

    # Путь к примеру фотографии (заглушка)
    example_photo_path = "bot/handlers/photo_2024-04-19_17-40-12.jpg"
    # Инструкция в форме фото
    await message.answer(instructions)
    # await message.answer_photo(types.FSInputFile(example_photo_path))
    # Инструкция в формате видео
    media = [
    InputMediaVideo(media=FSInputFile("bot/handlers/video/IMG_1434.MOV"), caption="Включите вспышку", width=448, height=848),
    InputMediaVideo(media=FSInputFile("bot/handlers/video/IMG_1436.MOV"), caption="фронтальная проекция", width=448, height=848),
    InputMediaVideo(media=FSInputFile("bot/handlers/video/IMG_1438.MOV"), caption="Нижняя проекция", width=448, height=848),
    InputMediaVideo(media=FSInputFile("bot/handlers/video/IMG_1440.MOV"), caption="Верхня Проекция", width=448, height=848),
    ]

    await message.answer_media_group(media=media)



# Добавляем команду для инструкции в главное меню
@router.message(F.text == "ℹ️ Инструкция")
async def show_instructions_command(message: types.Message):
    """Показ инструкции по запросу"""
    await log_event("user_action", "User requested instructions", message.from_user.id)
    logger.info(f"User {message.from_user.id} requested instructions")
    await show_instructions(message)



# --------------------- Система обратной связи ---------------------
@router.message(F.text == "📝 Обратная связь")
@router.message(Command("feedback"))
async def feedback_command(message: types.Message, state: FSMContext):
    """Запрос обратной связи"""
    await log_event("user_action", "User requested feedback", message.from_user.id)
    logger.info(f"User {message.from_user.id} requested feedback")
    await message.answer("Напишите ваш отзыв или предложение:", reply_markup=cancel_keyboard)
    await state.set_state(FeedbackStates.waiting_for_feedback)


@router.message(FeedbackStates.waiting_for_feedback)
async def process_feedback(message: types.Message, state: FSMContext):
    """Обработка полученного фидбека"""
    await log_event("feedback", message.text, message.from_user.id)
    logger.info(f"Feedback from {message.from_user.id}: {message.text}")
    await message.answer("✅ Спасибо за ваш отзыв!", reply_markup=main_keyboard)
    await state.clear()


# --------------------- Основной функционал ---------------------
# Функция загрузки фото
async def start_upload(message: types.Message, state: FSMContext, user_id: int):
    """Начало загрузки фото"""
    await log_event("user_action", "User started photo upload", user_id)
    logger.info(f"User {user_id} started photo upload")
    user_data[user_id] = {"photos": []}
    await message.answer("Отправьте до 3 фотографий зубов:", reply_markup=upload_keyboard)
    await state.set_state(UploadStates.waiting_for_photos)

# Вызов функции загрузки по обчной кнопке
@router.message(F.text == "📷 Загрузить фото")
async def start_upload_button(message: types.Message, state: FSMContext):
    """Начало загрузки фото через обычную кнопку"""
    await start_upload(message, state, user_id=message.from_user.id)

# Вызов функции загрузки по inline кнопке
@router.callback_query(F.data == "start_upload")
async def inline_start_upload(call: types.CallbackQuery, state: FSMContext):
    """Обработчик для кнопки загрузки фото через Inline-кнопку"""
    await call.message.edit_reply_markup()  # Убираем кнопки после нажатия
    await start_upload(call.message, state, user_id=call.from_user.id)

@router.message(UploadStates.waiting_for_photos, F.photo)
async def process_photo(message: types.Message, state: FSMContext):
    """Обработка полученных фото"""
    user_id = message.from_user.id
    user_data[user_id]["photos"].append(message.photo[-1].file_id)

    await log_event("user_action", f"User {user_id} uploaded photo {len(user_data[user_id]['photos'])}", user_id)
    logger.info(f"User {user_id} uploaded photo {len(user_data[user_id]['photos'])}")

    if len(user_data[user_id]["photos"]) >= 3:
        await message.answer("✅ Фото получены! Спасибо!", reply_markup=main_keyboard)
        await finish_upload(message, state)
        #await state.clear()
    else:
        await message.answer(f"✅ Фото {len(user_data[user_id]['photos'])}/3 принято!")


@router.message(UploadStates.waiting_for_photos, F.text == "✅ Готово")
async def finish_upload(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if not user_data.get(user_id) or len(user_data[user_id]["photos"]) == 0:
        await message.answer("❌ Нет фото для обработки", reply_markup=main_keyboard)
        return

    await message.answer("📡 Отправляю фото на обработку...")

    # Скачиваем и конвертируем фото
    photos_base64 = []
    for file_id in user_data[user_id]["photos"]:
        try:
            # Получаем файл из Telegram
            file = await message.bot.get_file(file_id)
            if not file.file_path:
                await log_event("error", f"Не удалось получить путь к файлу {file_id}")
                logger.error(f"Не удалось получить путь к файлу {file_id}")
                continue

            # Скачиваем содержимое
            file_data = await message.bot.download_file(file.file_path)

            # Конвертируем в base64
            encoded = base64.b64encode(file_data.read()).decode('utf-8')
            logger.info(f"Закодировано фото {file_id}, длина: {len(encoded)}")

            photos_base64.append(encoded)
        except Exception as e:
            await log_event("error", f"Ошибка обработки фото: {str(e)}")
            logger.error(f"Ошибка обработки фото: {str(e)}")
            continue

    # Формируем payload с base64
    payload = {
        "user_id": user_id,
        "photos": photos_base64
    }
    try:
        await send_to_save(payload)
    except Exception as e:
        await log_event("error", f"send_to_save ошибка: {str(e)}")
        logger.error(f"send_to_save ошибка: {str(e)}")
    try:
        response = await rpc_call(payload)
    except Exception as e:
        await log_event("error", f"RPC ошибка: {str(e)}")
        logger.error(f"RPC ошибка: {str(e)}")
        await message.answer("❌ Ошибка обработки", reply_markup=main_keyboard)
        return

    mouth_type = response.get("mouth_type", [])
    result_list = response.get("result_list", [])

    # Преобразуем mouth_type в русский текст
    type_mapping = {
        "Front view": "Передние зубы",
        "Upper Jaw": "Верхняя челюсть",
        "Lower Jaw": "Нижняя челюсть"
    }
    ru_type = [type_mapping.get(item, "Не распознано") for item in mouth_type]

    formatted_text = "🦷Результаты анализа зубов:\n" + "\n".join(
        f"📸 Фото {i + 1}: <b>{item}</b>" for i, item in enumerate(ru_type)
    )
    await message.answer(formatted_text, parse_mode="HTML")

    # Отправляем обработанные фото
    for photo_b64 in result_list:
        photo_bytes = base64.b64decode(photo_b64, validate=True)
        photo_file = BufferedInputFile(photo_bytes, filename="processed.jpg")
        await message.bot.send_photo(message.chat.id, photo_file)

    await message.answer(
        "Результаты обработки:\n"
        "🔴 Красный квадрат: Обнаружен кариес\n"
        "🔵 Синий квадрат: Подозрение на кариес",
        reply_markup=main_keyboard
    )

    await state.clear()
    user_data.pop(user_id, None)

    await asyncio.sleep(2)
    await message.answer(
        "Понравился ли вам результат анализа?\n"
        "Мы будем благодарны за ваш отзыв!",
        reply_markup=feedback_request_keyboard
    )
    await state.set_state(FeedbackStates.waiting_for_choice)


@router.message(UploadStates.waiting_for_photos, F.text == "❌ Отмена")
async def cancel_upload(message: types.Message, state: FSMContext):
    """Отмена загрузки фото"""
    await log_event("user_action", "User canceled upload", message.from_user.id)
    logger.info(f"User {message.from_user.id} canceled upload")
    await message.answer("Загрузка отменена", reply_markup=main_keyboard)
    await state.clear()