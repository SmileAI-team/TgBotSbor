import logging
from aiogram import Router, types, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import FSInputFile
from external_services.backend_requests import create_user_by_telegram, upload_files
from keyboards.user_keyboards import upload_keyboard, comment_keyboard, start_upload_keyboard
import httpx
from typing import Tuple
import os

# Инициализация логгера
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(filename)s:%(lineno)d #%(levelname)-8s '
           '[%(asctime)s] - %(name)s - %(message)s')

router = Router()

# Класс для определения состояний загрузки фотографий и комментариев
class UploadStates(StatesGroup):
    waiting_for_photo = State()
    waiting_for_comment = State()

# Словарь для временного хранения данных пользователя
user_data = {}

# Обработчик команды /start
@router.message(CommandStart())

async def send_welcome(message: types.Message):
    """
    Приветственное сообщение при старте бота. Создает пользователя в базе по его Telegram ID.
    """
    await message.answer("Привет! Этот бот поможет тебе узнать в каком состоянии твои зубки🦷")

    telegram_id = str(message.from_user.id)

    try:
        logger.info(f"Sending request to API with params {telegram_id}")
        response = await create_user_by_telegram(telegram_id)
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response content: {response.json()}")
        if response.status_code == 200:
            # await message.answer("Поздравляю, Вы добавлены в базу!")
            await message.answer("Чтобы загрузить фото, используй команду /upload", reply_markup=start_upload_keyboard)
        elif response.status_code == 201:
            # await message.answer("Поздравляю, Вы уже добавлены в базу!")
            await message.answer("Чтобы загрузить фото, используй команду /upload", reply_markup=start_upload_keyboard)
        else:
            await message.answer("Произошла ошибка при создании пользователя.")
    except httpx.RequestError as e:
        logger.error(f"Failed to create user: {e}")
        await message.answer("Произошла ошибка при подключении к серверу.")


# Обработчик команды /upload
@router.message(Command(commands=['upload']))
async def start_upload(message: types.Message, state: FSMContext):
    """
    Начало процесса загрузки фотографий.
    """
    user_data[message.from_user.id] = {'photos': [], 'comment': ''}
    photo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "photos", "front.jpg")
    photo = FSInputFile(photo_path)
    await message.answer_photo(
        photo=photo,
        text="Отправьте фото фронтальной проекции зубов.",
        caption="Отправьте фото фронтальной проекции зубов.",
        reply_markup=upload_keyboard)
    await state.set_state(UploadStates.waiting_for_photo)


# Обработчик инлайн команды start_upload
@router.callback_query(lambda call: call.data == 'start_upload')
async def handle_start_upload(call: types.CallbackQuery, state: FSMContext):
    """
    Начало процесса загрузки фотографий по инлайн кнопке.
    """
    user_id = call.from_user.id
    user_data[user_id] = {'photos': [], 'comment': ''}
    photo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "photos", "front.jpg")
    photo=FSInputFile(photo_path)
    await call.message.answer_photo(
        photo=photo,
        #text="Отправьте фото фронтальной проекции зубов.",
        caption="Отправьте фото фронтальной проекции зубов.",
        reply_markup=upload_keyboard)
    await state.set_state(UploadStates.waiting_for_photo)
    await call.answer()

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
