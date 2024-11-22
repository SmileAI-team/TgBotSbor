import logging
from aiogram import Router, types, F, Bot
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import FSInputFile
from external_services.backend_requests import create_user_by_telegram, upload_files
from keyboards.user_keyboards import upload_keyboard, comment_keyboard, start_upload_keyboard, consent_keyboard, ready_keyboard
import os
import cv2
import numpy as np
from io import BytesIO

# Инициализация логгера
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(filename)s:%(lineno)d #%(levelname)-8s %(message)s'
)

router = Router()

class ConsentStates(StatesGroup):
    waiting_for_consent = State()

# Класс для определения состояний загрузки фотографий и комментариев
class UploadStates(StatesGroup):
    waiting_for_front_teeth_photo = State()
    waiting_for_upper_teeth_gums_photo = State()
    waiting_for_lower_teeth_gums_photo = State()
    waiting_for_photo = State()
    waiting_for_comment = State()

# Словарь для временного хранения данных пользователя
user_data = {}

# Обработчик команды /start
@router.message(CommandStart())
async def send_welcome(message: types.Message, state: FSMContext):
    """
    Приветственное сообщение при старте бота. Создает пользователя в базе по его Telegram ID.
    """
    await message.answer("Добро пожаловать! Этот бот поможет провести диагностику состояния зубов \
с использованием фотографий и искусственного интеллекта. Вы получите предварительные \
рекомендации по уходу за зубами, но это не заменяет визит к стоматологу🦷")

    await message.answer("Для использования нашего сервиса требуется ваше согласие на обработку персональных данных, \
включая фотографии полости рта. Эти данные будут использоваться только для диагностики и предоставления рекомендаций. \
Вы можете ознакомиться с [Политикой конфиденциальности](https://example.com/privacy).",
                         reply_markup=consent_keyboard)
    await state.set_state(ConsentStates.waiting_for_consent)

# Обработчик согласия на обработку данных
@router.callback_query(lambda call: call.data in ["consent_yes", "consent_no"])
async def handle_consent(call: types.CallbackQuery, state: FSMContext):
    if call.data == "consent_yes":
        await call.message.answer("Спасибо за доверие! Теперь перейдем к подготовке к диагностике. /upload", reply_markup=start_upload_keyboard)
        await state.clear()
    else:
        await call.message.answer("К сожалению, без вашего согласия на обработку персональных данных диагностика невозможна. Если вы передумаете, просто запустите бота снова /start.")
        await state.clear()
    await call.answer()

# Обработчик команды /upload
@router.message(Command(commands=['upload']))
async def start_upload(message: types.Message, state: FSMContext):
    """
    Начало процесса загрузки фотографий.
    """
    user_data[message.from_user.id] = {'photos': [], 'comment': ''}
    await send_preparation_instructions(message)

async def send_preparation_instructions(message: types.Message):
    """
    Отправка инструкции по подготовке к съемке.
    """
    instructions = (
        "Перед тем как сделать фото, пожалуйста, следуйте этим советам:\n"
        "1. Найдите хорошо освещенное место.\n"
        "2. Используйте вспышку, если это необходимо.\n"
        "3. Протрите камеру, чтобы избежать размытых изображений.\n\n"
        "Когда будете готовы, нажмите 'Готово'."
    )
    await message.answer(instructions, reply_markup=ready_keyboard)

# Обработчик инлайн команды ready
@router.callback_query(lambda call: call.data == 'ready')
async def handle_ready(call: types.CallbackQuery, state: FSMContext):
    """
    Обработка нажатия кнопки 'Готово' и запрос первой фотографии.
    """
    await request_front_teeth_photo(call.message)
    await state.set_state(UploadStates.waiting_for_front_teeth_photo)

# Функции для запроса фотографий
async def request_front_teeth_photo(message: types.Message):
    instructions = (
        "Пожалуйста, сделайте фото передних зубов.\n"
        "Когда фото будет готово, отправьте его в чат."
    )
    await message.answer(instructions)

async def request_upper_teeth_gums_photo(message: types.Message):
    instructions = (
        "Пожалуйста, сделайте фото верхних зубов и десен.\n"
        "Когда фото будет готово, отправьте его в чат."
    )
    await message.answer(instructions)

async def request_lower_teeth_gums_photo(message: types.Message):
    instructions = (
        "Пожалуйста, сделайте фото нижних зубов и десен.\n"
        "Когда фото будет готово, отправьте его в чат."
    )
    await message.answer(instructions)

# Обработчики для получения фотографий
@router.message(UploadStates.waiting_for_front_teeth_photo)
async def handle_front_teeth_photo(message: types.Message, state: FSMContext):
    photo = message.photo[-1]
    if await is_photo_blurry(message.bot, photo):
        await message.answer("Фото получилось нечетким. Пожалуйста, попробуйте сделать его снова.")
        return
    user_data[message.from_user.id]['photos'].append(photo.file_id)
    await request_upper_teeth_gums_photo(message)
    await state.set_state(UploadStates.waiting_for_upper_teeth_gums_photo)

@router.message(UploadStates.waiting_for_upper_teeth_gums_photo)
async def handle_upper_teeth_gums_photo(message: types.Message, state: FSMContext):
    photo = message.photo[-1]
    if await is_photo_blurry(message.bot, photo):
        await message.answer("Фото получилось нечетким. Пожалуйста, попробуйте сделать его снова.")
        return
    user_data[message.from_user.id]['photos'].append(photo.file_id)
    await request_lower_teeth_gums_photo(message)
    await state.set_state(UploadStates.waiting_for_lower_teeth_gums_photo)

@router.message(UploadStates.waiting_for_lower_teeth_gums_photo)
async def handle_lower_teeth_gums_photo(message: types.Message, state: FSMContext):
    photo = message.photo[-1]
    if await is_photo_blurry(message.bot, photo):
        await message.answer("Фото получилось нечетким. Пожалуйста, попробуйте сделать его снова.")
        return
    user_data[message.from_user.id]['photos'].append(photo.file_id)
    await message.answer("Спасибо! Все фотографии получены.")
    await state.clear()

# Обработчик инлайн команды start_upload
@router.callback_query(lambda call: call.data == 'start_upload')
async def handle_start_upload(call: types.CallbackQuery, state: FSMContext):
    """
    Начало процесса загрузки фотографий по инлайн кнопке.
    """
    user_data[call.from_user.id] = {'photos': [], 'comment': ''}
    await send_preparation_instructions(call.message)

# Обработчик загрузки фотографии
@router.callback_query(lambda call: call.data == 'upload_photo')
async def handle_photo_upload_callback(call: types.CallbackQuery, state: FSMContext):
    """
    Обработка полученной фотографии.
    """
    await call.message.answer("Пожалуйста, отправьте фото как изображение. 📎")
    await call.answer()

# Запрос на отрпавку комментари к 3 фото
@router.message(UploadStates.waiting_for_photo, F.photo)
async def handle_photo(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user_data[user_id]['photos'].append(message.photo[-1].file_id)
    photos_count = len(user_data[user_id]['photos'])
    logger.info(f"User {user_id} uploaded photo {photos_count}.")

    # Check if all 3 photos are uploaded
    if photos_count == 1:
        photo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "photos", "upper.jpg")
        photo=FSInputFile(photo_path)
        await message.answer_photo(
            photo=photo,
            caption="Фото фронтальной проекции получено, загрузите фото верхних зубов.",
            reply_markup=upload_keyboard)
    elif photos_count == 2:
        photo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "photos", "lower.jpg")
        photo=FSInputFile(photo_path)
        await message.answer_photo(
            photo=photo,
            caption="Фото верхней проекции получено, загрузите фото нижних зубов.",
            reply_markup=upload_keyboard)
    elif photos_count == 3:
        await message.answer("Все 3 фото получены. Отправьте комментарий или используйте команду /skip для пропуска комментария.", reply_markup=comment_keyboard)
        await state.set_state(UploadStates.waiting_for_comment)


# Функция прерывания отправки фото
@router.callback_query(lambda call: call.data == 'skip_photo')
async def skip_photo(call: types.CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    logger.info(f"User {user_id} chose to skip photo upload.")
    # Add dummy photos to simulate 3 photo uploads
    user_data[user_id]['photos'] += ["dummy_photo_id"] * (3 - len(user_data[user_id]['photos']))
    await call.message.answer("Все 3 фото получены. Отправьте комментарий или используйте команду /skip для пропуска комментария.", reply_markup=comment_keyboard)
    await state.set_state(UploadStates.waiting_for_comment)
    try:
        await call.answer()
    except Exception as e:
        logger.error(f"Failed to answer callback query: {e}")

# Функция отправки фото с коментарием NO comment
@router.callback_query(lambda call: call.data == 'skip_comment')
async def skip_comment(call: types.CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    logger.info(f"User {user_id} chose to skip comment.")
    await send_photos_to_backend(call.message, user_id, user_data[user_id]['photos'], 'NO comments')
    await state.clear()
    try:
        await call.answer()
    except Exception as e:
        logger.error(f"Failed to answer callback query: {e}")

# Функция отправки фото с комментариями
@router.message(UploadStates.waiting_for_comment)
async def handle_comment(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user_data[user_id]['comment'] = message.text
    logger.info(f"User {user_id} provided a comment.")
    await send_photos_to_backend(message, user_id, user_data[user_id]['photos'], message.text)
    await state.clear()


# Функция отправки фотографий на сервер
async def send_photos_to_backend(message: types.Message, user_id: int, photos: list, comment: str):
    """
    Отправка фотографий и комментария на бэкенд.
    """
    photo_files = []
    for idx, photo_id in enumerate(photos):
        logger.info(f"Processing photo {idx+1} for user {user_id}.")
        if photo_id != "dummy_photo_id":  # Check if the photo is not a dummy
            photo = await message.bot.get_file(photo_id)
            file = await message.bot.download_file(photo.file_path)
            photo_files.append((f"photo_{idx}.jpg", file.read()))

    logger.info(f"Uploading photos to backend for user {user_id} with comment: {comment}")
    try:
        response = await upload_files(str(user_id), photo_files, comment)

        if "detail" in response and "Mouth not detected" in response["detail"]:
            await message.answer("На фотографиях не обнаружены зубы.", reply_markup=start_upload_keyboard)
        elif "detail" in response and "Success" in response["detail"]:
            await message.answer("Фотографии загружены в базу. Вы можете загрузить следующии фотографии командой /upload", reply_markup=start_upload_keyboard)
        else:
            await message.answer("Произошла неизвестная ошибка при загрузке фотографий. Попробуйте снова.", reply_markup=types.ReplyKeyboardRemove())

    except Exception as e:
        logger.error(f"Failed to upload photos: {e}")
        await message.answer("Произошла ошибка при загрузке фотографий. Попробуйте снова.", reply_markup=types.ReplyKeyboardRemove())

async def is_photo_blurry(bot: Bot, photo: types.PhotoSize) -> bool:
    """
    Проверяет, является ли фото нечетким.
    """
    file_info = await bot.get_file(photo.file_id)
    file = await bot.download_file(file_info.file_path)
    file_bytes = BytesIO(file.read())
    image = np.asarray(bytearray(file_bytes.read()), dtype="uint8")
    image = cv2.imdecode(image, cv2.IMREAD_GRAYSCALE)
    laplacian_var = cv2.Laplacian(image, cv2.CV_64F).var()
    print(laplacian_var)
    return laplacian_var < 1  # Пороговое значение для определения нечеткости

# Обработчик команды /analyze данную функцию допишем позже
async def analyze_and_send_results(bot: Bot, message: types.Message, photos: list):
    """
    Анализирует фотографии и отправляет результаты пользователю.
    """
    results = []
    for photo_id in photos:
        photo = await bot.get_file(photo_id)
        file = await bot.download_file(photo.file_path)
        file_bytes = BytesIO(file.read())
        image = np.asarray(bytearray(file_bytes.read()), dtype="uint8")
        image = cv2.imdecode(image, cv2.IMREAD_GRAYSCALE)

        # Пример анализа изображения (MVP)
        laplacian_var = cv2.Laplacian(image, cv2.CV_64F).var()
        if laplacian_var < 1:
            results.append("Фото нечеткое.")
        else:
            # Пример анализа (будет доработан в будущем)
            if detect_caries(image):
                results.append("Обнаружен кариес.")
            elif detect_plaque(image):
                results.append("Обнаружен налет.")
            else:
                results.append("Идеальные зубы.")

    # Отправка результатов пользователю
    result_message = "\n".join(results)
    await message.answer(result_message)

def detect_caries(image):
    # Пример функции для обнаружения кариеса (будет доработана в будущем)
    return False

def detect_plaque(image):
    # Пример функции для обнаружения налета (будет доработана в будущем)
    return False
