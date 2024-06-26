import json
import aiohttp
import io
from fastapi import HTTPException
from aiohttp import FormData
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

async def upload_file(file_name: str, folder_id: str, file_content: io.BytesIO):
    url = "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart"

    # Создание FormData для правильной передачи данных
    form = FormData()
    metadata = {
        "name": file_name,
        "parents": [folder_id]
    }
    form.add_field('metadata',
                   value=json.dumps(metadata),
                   content_type='application/json')
    form.add_field('file',
                   value=file_content,
                   filename=file_name,
                   content_type='application/octet-stream')

    access_token = await get_access_token()
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=form, headers=headers) as response:
            if response.status != 200:
                raise HTTPException(status_code=response.status, detail=await response.text())
            return await response.json()