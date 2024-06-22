import json
import aiohttp
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from core.config import settings

SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = 'smile-ai-bot-1dccd401d6ed.json'

# Загрузка учетных данных
credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)

async def get_access_token():
    credentials.refresh(Request())
    return credentials.token

async def create_folder(folder_name: str, parent_folder_id: str = None) -> str:
    access_token = await get_access_token()
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder',
    }
    if parent_folder_id:
        file_metadata['parents'] = [parent_folder_id]

    async with aiohttp.ClientSession() as session:
        async with session.post(
            'https://www.googleapis.com/drive/v3/files',
            headers=headers,
            data=json.dumps(file_metadata)
        ) as response:
            if response.status != 200:
                raise Exception(f"Error creating folder: {response.status}")
            result = await response.json()
            return f"https://drive.google.com/drive/folders/{result['id']}"