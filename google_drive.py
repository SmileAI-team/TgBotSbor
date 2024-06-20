from google.oauth2 import service_account
from googleapiclient.discovery import build
from core.config import settings

SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = 'smile-ai-bot-1dccd401d6ed.json'  # Путь к файлу с ключом

credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=credentials)

def create_folder(folder_name: str, parent_folder_id: str = None) -> str:
    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('drive', 'v3', credentials=credentials)  # Перемещаем создание service сюда

    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder',
    }
    if parent_folder_id:
        file_metadata['parents'] = [parent_folder_id]

    file = service.files().create(body=file_metadata, fields='id').execute()
    return f"https://drive.google.com/drive/folders/{file.get('id')}"
