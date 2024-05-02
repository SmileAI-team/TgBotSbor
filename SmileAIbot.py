# импорт необходимых библиотек
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, CallbackContext
import nest_asyncio
import requests
from io import BytesIO
from googleapiclient.http import MediaIoBaseUpload
import sqlite3
import os
from datetime import datetime
import json


# Устанавливаем зависимости
path = './'
db_path = f'{path}/bot_data.db'
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

TTOKEN = config['TTOKEN']
root_folder_id = config['root_folder_id']

# Задаем правам для админов и дата саентистов
permissions = [
    {'email': 'adminsmileaibot@googlegroups.com', 'role': 'writer'},
    {'email': 'dssmileaibot@googlegroups.com', 'role': 'reader'}
]


# Создаем подключение к Drive
SERVICE_ACCOUNT_FILE = f"{path}/smile-ai-bot-1dccd401d6ed.json"
SCOPES = ['https://www.googleapis.com/auth/drive.file']

credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)

service = build('drive', 'v3', credentials=credentials)

# Создание папки
def create_folder_and_set_permissions(service, folder_name, parent_id=None, permissions=None):
    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_id] if parent_id else []
    }
    folder = service.files().create(body=file_metadata, fields='id').execute()
    folder_id = folder.get('id')

    # Установка разрешений для разных групп
    if permissions:
        for perm in permissions:
            user_permission = {
                'type': 'group',
                'role': perm['role'],
                'emailAddress': perm['email']
            }
            service.permissions().create(
                fileId=folder_id,
                body=user_permission,
                fields='id',
            ).execute()

    return folder_id
# Функции для загрузки файла
def upload_file(file_name, file_path, folder_id):
    file_metadata = {
        'name': file_name,
        'parents': [folder_id]
    }
    media = MediaFileUpload(file_path, mimetype='image/jpeg')
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    return file.get('id')

# Функция загрузки файлов в оперативную память
def download_file_to_memory(url):
    response = requests.get(url)
    if response.status_code == 200:
        return BytesIO(response.content)
    else:
        raise Exception(f"Не удалось загрузить файл: статус код {response.status_code}")

# Функция загрузки файла из памяти в гугл драйв
def upload_file_from_memory(service, file_stream, file_name, folder_id, mime_type='image/jpeg'):
    file_metadata = {
        'name': file_name,
        'parents': [folder_id]
        }
    media = MediaIoBaseUpload(file_stream, mimetype=mime_type, resumable=True)
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    return file.get('id')


# Блок для базы данныйх
def init_db():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS user_folders (user_id INTEGER PRIMARY KEY, folder_id TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS sessions (
                    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    folder_id TEXT,
                    creation_date DATETIME DEFAULT CURRENT_TIMESTAMP
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS files (
                    file_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER,
                    file_name TEXT,
                    file_path TEXT,
                    upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions (session_id)
                )''')
    conn.commit()
    conn.close()

init_db()

def save_user_folder(user_id, folder_id):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO user_folders (user_id, folder_id) VALUES (?, ?)', (user_id, folder_id))
    conn.commit()
    conn.close()

def get_user_folder(user_id):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('SELECT folder_id FROM user_folders WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None


# Основные функции бота
async def start(update: Update, context: CallbackContext):
    handle_existing_or_new_folder(update, context)
    keyboard = [
        [KeyboardButton("Загрузить фото верхних зубов")],
        [KeyboardButton("Загрузить фото нижних зубов")],
        [KeyboardButton("Загрузить фронтальную проекцию")],
        [KeyboardButton("Загрузить анамнез")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
    await update.message.reply_text('Выберите действие:', reply_markup=reply_markup)


def handle_existing_or_new_folder(update, context):
    context.user_data['user_id'] = update.effective_user.id
    folder_id = get_user_folder(context.user_data['user_id'])
    permissions = [
        {'email': 'adminsmileaibot@googlegroups.com', 'role': 'writer'},
        {'email': 'dssmileaibot@googlegroups.com', 'role': 'reader'}
    ]

    if folder_id is None:
        user_name = update.effective_user.first_name
        folder_name = f"Folder_for_{context.user_data['user_id']}_{user_name}"
        folder_id = create_folder_and_set_permissions(service, folder_name, root_folder_id, permissions)
        save_user_folder(context.user_data['user_id'], folder_id)
        message = "Ваша персональная папка создана!"
    else:
        message = "Ваша персональная папка уже существует!"
    context.user_data['folder_id'] = folder_id

async def handle_text(update: Update, context: CallbackContext):
    text = update.message.text
    if text == "Загрузить фото верхних зубов":
        context.user_data['expected_file'] = 'upload_upper_teeth'
        await update.message.reply_text("Пожалуйста, загрузите фото верхних зубов.")
    elif text == "Загрузить фото нижних зубов":
        context.user_data['expected_file'] = 'upload_lower_teeth'
        await update.message.reply_text("Пожалуйста, загрузите фото нижних зубов.")
    elif text == "Загрузить фронтальную проекцию":
        context.user_data['expected_file'] = 'upload_frontal_projection'
        await update.message.reply_text("Пожалуйста, загрузите фронтальную проекцию.")
    elif text == "Загрузить анамнез":
        context.user_data['expected_file'] = 'upload_anamnesis'
        await update.message.reply_text("Пожалуйста, загрузите текстовый файл с анамнезом.")

async def handle_document(update: Update, context: CallbackContext):
    document = update.message.document
    if document.mime_type == "text/plain":
        file = await document.get_file()
        file_path = file.file_path
        file_stream = download_file_to_memory(file_path)
        folder_id = await create_session_folder(context, context.user_data['user_id'])
        #folder_id = context.user_data['folder_id']
        file_name = "anamnes.txt"
        upload_file_from_memory(service, file_stream, file_name, folder_id)
        save_file_record(context.user_data['latest_session_id'], file_name, file_path)
        await update.message.reply_text("Текстовый файл успешно загружен.")


async def handle_photo(update: Update, context: CallbackContext):
    """Обрабатывает загрузку фотографии."""
    photo = update.message.photo[-1]
    bot = Bot(token=context.bot.token)  # Создаем экземпляр бота
    file = await bot.get_file(photo.file_id)  # Получаем объект файла
    file_path = file.file_path
    # Загрузка файла в память
    file_stream = download_file_to_memory(file_path)
    folder_id = await create_session_folder(context, context.user_data['user_id'])
    #folder_id = context.user_data['folder_id']


    if context.user_data.get('expected_file') == 'upload_upper_teeth':
        file_name = "upper_teeth.jpg"
        upload_file_from_memory(service, file_stream, file_name, folder_id)
        save_file_record(context.user_data['latest_session_id'], file_name, file_path)
        await update.message.reply_text("Фото верхних зубов загружено.")

    elif context.user_data.get('expected_file') == 'upload_lower_teeth':
        file_name = "lower_teeth.jpg"
        upload_file_from_memory(service, file_stream, file_name, folder_id)
        save_file_record(context.user_data['latest_session_id'], file_name, file_path)
        await update.message.reply_text("Фото нижних зубов загружено.")

    elif context.user_data.get('expected_file') == 'upload_frontal_projection':
        file_name = "frontal_projection.jpg"
        upload_file_from_memory(service, file_stream, file_name, folder_id)
        save_file_record(context.user_data['latest_session_id'], file_name, file_path)
        await update.message.reply_text("Фронтальная проекция загружена.")

def error_handler(update: object, context: CallbackContext) -> None:
    """Log Errors caused by Updates."""
    print(f"Ошибка: {context.error}")  # Или используйте logging
    try:
        raise context.error
    except AttributeError as e:
        print(f"Ошибка атрибута: {str(e)}")  # Можно отправить сообщение об ошибке пользователю
    except Exception as e:
        print(f"Необработанная ошибка: {str(e)}")  # Можно отправить сообщение об ошибке пользователю


# Вспомогательный функции бота
def get_latest_session_id(user_id):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('SELECT session_id FROM sessions WHERE user_id = ? ORDER BY creation_date DESC LIMIT 1', (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def count_files_in_session(session_id):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM files WHERE session_id = ?', (session_id,))
    count = c.fetchone()[0]
    conn.close()
    return count

def create_new_session(user_id, folder_id):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('INSERT INTO sessions (user_id, folder_id) VALUES (?, ?)', (user_id, folder_id))
    conn.commit()
    new_session_id = c.lastrowid
    conn.close()
    return new_session_id
def save_file_record(session_id, file_name, file_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('INSERT INTO files (session_id, file_name, file_path) VALUES (?, ?, ?)', (session_id, file_name, file_path))
    conn.commit()
    conn.close()


async def create_session_folder(context, user_id):
    context.user_data['latest_session_id'] = get_latest_session_id(user_id)
    if context.user_data['latest_session_id'] is None or count_files_in_session(context.user_data['latest_session_id']) >= 4:
        # Создаем новую папку сессии на Google Drive
        new_folder_name = f"Session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        new_folder_id = create_folder_and_set_permissions(service, new_folder_name, context.user_data['folder_id'], permissions)
        context.user_data['latest_session_id'] = create_new_session(user_id, new_folder_id)
        return new_folder_id
    else:
        # Получаем folder_id для последней сессии из базы данных
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute('SELECT folder_id FROM sessions WHERE session_id = ?', (context.user_data['latest_session_id'],))
        folder_id = c.fetchone()[0]
        conn.close()
        # Возвращаем folder_id для последней сессии
        return folder_id
    


def main():
    application = Application.builder().token(TTOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    application.run_polling()

if __name__ == '__main__':
    nest_asyncio.apply()
    main()
