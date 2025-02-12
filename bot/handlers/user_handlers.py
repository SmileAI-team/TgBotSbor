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
    privacy_policy_link = "<a href='https://example.com/privacy'>Политикой конфиденциальности</a>"
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
        "Если вы передумаете, нажмите /start, чтобы снова ознакомиться с Политикой конфиденциальности.",
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
        await state.clear()
    else:
        await message.answer(f"✅ Фото {len(user_data[user_id]['photos'])}/3 принято!")


@router.message(UploadStates.waiting_for_photos, F.text == "✅ Готово")
async def finish_upload(message: types.Message, state: FSMContext):
    """Завершение загрузки фото с отправкой на обработку"""
    user_id = message.from_user.id
    if len(user_data[user_id]["photos"]) == 0:
        await message.answer("❌ Вы не отправили ни одной фотографии. Попробуйте снова.")
        return
    await message.answer("📡 Отправляю фото на обработку...")
    photos_base64 = []
    for file_id in user_data[user_id]["photos"]:
        file = await message.bot.get_file(file_id)
        file_path = file.file_path
        file_bytes_obj = await message.bot.download_file(file_path)
        # Преобразуем полученные байты в base64 (предполагается, что file_bytes_obj — BytesIO)
        b64_encoded = base64.b64encode(file_bytes_obj.getvalue()).decode("utf-8")
        photos_base64.append(b64_encoded)
    payload = {
        "user_id": user_id,
        "photos": photos_base64,
    }
    try:
        response = await rpc_call(payload)
    except Exception as e:
        await message.answer("❌ Ошибка связи с сервером обработки")
        return
    if response.get("error"):
        await message.answer(f"❌ Ошибка обработки: {response['error']}")
    else:
        result_list = response.get("result_list", [])
        result_dict = response.get("result_dict", {})
        await message.answer("✅ Фото обработаны, отправляю результат!")
        for photo_b64 in result_list:
            photo_bytes = base64.b64decode(photo_b64)
            # Создаем InputFile из байтов
            photo_file = BufferedInputFile(
                photo_bytes,
                filename="processed_image.jpg"
            )
            await message.bot.send_photo(
                chat_id=message.chat.id,
                photo=photo_file
            )
        await message.answer(f"Результаты обработки: {result_dict}")
    await state.clear()
    user_data.pop(user_id, None)


@router.message(UploadStates.waiting_for_photos, F.text == "❌ Отмена")
async def cancel_upload(message: types.Message, state: FSMContext):
    """Отмена загрузки фото"""
    logger.info(f"User {message.from_user.id} canceled upload")
    await message.answer("Загрузка отменена", reply_markup=main_keyboard)
    await state.clear()