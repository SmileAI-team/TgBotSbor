import asyncio
import logging
from io import BytesIO
from aiogram.types import BufferedInputFile
from aiogram import Router, types, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from ..keyboards.user_keyboards import *
from ..queue.rabbitmq_client import rpc_call
import base64

# Инициализация логгера
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
router = Router()

user_data = {}


class ConsentStates(StatesGroup):
    waiting_for_consent = State()


class UploadStates(StatesGroup):
    waiting_for_photos = State()


class FeedbackStates(StatesGroup):
    waiting_for_feedback = State()


# --------------------- Базовые обработчики ---------------------
@router.message(CommandStart())
async def start(message: types.Message, state: FSMContext):
    """Обработчик старта бота с приветствием и запросом согласия"""
    logger.info(f"User {message.from_user.id} started bot")

    # Приветственное сообщение
    await message.answer(
        "Добро пожаловать! Этот бот поможет провести диагностику состояния зубов "
        "с использованием фотографий и искусственного интеллекта. Вы получите "
        "предварительные рекомендации по уходу за зубами, но это не заменяет "
        "визит к стоматологу 🦷"
    )

    # Сообщение с согласием и ссылкой
    privacy_policy_link = "<a href='https://docs.google.com/document/d/1vBwBFJbYjn_jLhNvjALf_auXysNFzPmdh0mE6XV0_YI/edit?usp=sharing'>Пользовательским соглашением</a>"
    await message.answer(
        f"Для использования нашего сервиса требуется ваше согласие на обработку "
        f"персональных данных, включая фотографии полости рта. Эти данные будут "
        f"использоваться только для диагностики и предоставления рекомендаций. "
        f"Вы можете ознакомиться с {privacy_policy_link}.",
        parse_mode="HTML",
        reply_markup=consent_keyboard  # Показываем только кнопки согласия
    )
    await state.set_state(ConsentStates.waiting_for_consent)


@router.callback_query(ConsentStates.waiting_for_consent, F.data == "consent_yes")
async def consent_yes(call: types.CallbackQuery, state: FSMContext):
    """Обработка согласия с показом инструкции"""
    logger.info(f"User {call.from_user.id} gave consent")
    await call.message.edit_reply_markup()  # Убираем кнопки согласия

    # Сообщение о том, что можно ознакомиться с инструкцией
    await call.message.answer("✅ Отлично! Теперь вы можете ознакомиться с инструкцией:", reply_markup=main_keyboard)

    # Отправка инструкции
    await show_instructions(call.message)

    await state.clear()


@router.callback_query(ConsentStates.waiting_for_consent, F.data == "consent_no")
async def consent_no(call: types.CallbackQuery, state: FSMContext):
    """Обработка отказа"""
    logger.info(f"User {call.from_user.id} declined consent")
    await call.message.edit_reply_markup()  # Убираем кнопки согласия

    # Сообщение об отказе
    await call.message.answer(
        "❌ Без согласия использование бота невозможно. "
        "Если вы передумаете, нажмите /start, чтобы снова ознакомиться с Пользовательским соглашением.",
        reply_markup=types.ReplyKeyboardRemove()  # Убираем все клавиатуры
    )
    await state.clear()


async def show_instructions(message: types.Message):
    """Функция показа инструкции с фото"""
    instructions = (
        "Перед тем как сделать фото, пожалуйста, следуйте этим советам:\n"
        "1. Найдите хорошо освещенное место.\n"
        "2. Используйте вспышку, если это необходимо.\n"
        "3. Протрите камеру, чтобы избежать размытых изображений."
    )

    # Путь к примеру фотографии (заглушка)
    example_photo_path = "bot/handlers/photo_2024-04-19_17-40-12.jpg"

    await message.answer(instructions)
    await message.answer_photo(types.FSInputFile(example_photo_path))


# Добавляем команду для инструкции в главное меню
@router.message(F.text == "ℹ️ Инструкция")
async def show_instructions_command(message: types.Message):
    """Показ инструкции по запросу"""
    logger.info(f"User {message.from_user.id} requested instructions")
    await show_instructions(message)


@router.callback_query(ConsentStates.waiting_for_consent, F.data == "consent_no")
async def consent_no(call: types.CallbackQuery, state: FSMContext):
    """Обработка отказа"""
    logger.info(f"User {call.from_user.id} declined consent")
    await call.message.edit_reply_markup()
    await call.message.answer("❌ Без согласия использование бота невозможно")
    await state.clear()


# --------------------- Система обратной связи ---------------------
@router.message(F.text == "📝 Обратная связь")
@router.message(Command("feedback"))
async def feedback_command(message: types.Message, state: FSMContext):
    """Запрос обратной связи"""
    logger.info(f"User {message.from_user.id} requested feedback")
    await message.answer("Напишите ваш отзыв или предложение:", reply_markup=cancel_keyboard)
    await state.set_state(FeedbackStates.waiting_for_feedback)


@router.message(FeedbackStates.waiting_for_feedback)
async def process_feedback(message: types.Message, state: FSMContext):
    """Обработка полученного фидбека"""
    logger.info(f"Feedback from {message.from_user.id}: {message.text}")
    await message.answer("✅ Спасибо за ваш отзыв!", reply_markup=main_keyboard)
    await state.clear()


# --------------------- Основной функционал ---------------------
@router.message(F.text == "📷 Загрузить фото")
async def start_upload(message: types.Message, state: FSMContext):
    """Начало загрузки фото"""
    logger.info(f"User {message.from_user.id} started photo upload")
    user_data[message.from_user.id] = {"photos": []}
    await message.answer("Отправьте до 3 фотографий зубов:", reply_markup=upload_keyboard)
    await state.set_state(UploadStates.waiting_for_photos)


@router.message(UploadStates.waiting_for_photos, F.photo)
async def process_photo(message: types.Message, state: FSMContext):
    """Обработка полученных фото"""
    user_id = message.from_user.id
    user_data[user_id]["photos"].append(message.photo[-1].file_id)

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
                logger.error(f"Не удалось получить путь к файлу {file_id}")
                continue

            # Скачиваем содержимое
            file_data = await message.bot.download_file(file.file_path)

            # Конвертируем в base64
            encoded = base64.b64encode(file_data.read()).decode('utf-8')
            logger.info(f"Закодировано фото {file_id}, длина: {len(encoded)}")

            photos_base64.append(encoded)
        except Exception as e:
            logger.error(f"Ошибка обработки фото: {str(e)}")
            continue

    # Формируем payload с base64
    payload = {
        "user_id": user_id,
        "photos": photos_base64
    }

    try:
        response = await rpc_call(payload)
    except Exception as e:
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


@router.message(UploadStates.waiting_for_photos, F.text == "❌ Отмена")
async def cancel_upload(message: types.Message, state: FSMContext):
    """Отмена загрузки фото"""
    logger.info(f"User {message.from_user.id} canceled upload")
    await message.answer("Загрузка отменена", reply_markup=main_keyboard)
    await state.clear()