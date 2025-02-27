import aiohttp
import base64
import json
import logging
from pathlib import Path
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from datetime import datetime

logger = logging.getLogger(__name__)


class GoogleDriveClient:
    def __init__(self, credentials_path: str):
        self.credentials_path = credentials_path
        self.session = None
        self.credentials = None

    async def connect(self):
        """Инициализация подключения к Google Drive"""
        try:
            logger.info("Initializing Google Drive connection...")

            # Загрузка учетных данных
            self.credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path,
                scopes=['https://www.googleapis.com/auth/drive']
            )

            # Синхронное обновление токена
            request = Request()
            self.credentials.refresh(request)

            if not self.credentials.valid:
                raise RuntimeError("Invalid credentials after refresh")

            # Создание асинхронной сессии
            self.session = aiohttp.ClientSession()
            logger.info("Successfully connected to Google Drive")

        except Exception as e:
            logger.critical(f"Connection failed: {str(e)}")
            self.session = None
            raise

    async def create_folder_structure(self, user_id: str) -> str:
        """Создание структуры папок"""
        try:
            logger.info(f"Creating folder structure for user {user_id}")

            # Проверка подключения
            if not self.session or not self.credentials.valid:
                await self.connect()

            # Создаем папку пользователя
            user_folder = f"User_{user_id}"
            user_folder_id = await self._get_or_create_folder(
                name=user_folder,
                mime_type="application/vnd.google-apps.folder"
            )

            # Создаем папку сессии
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            session_folder_id = await self._get_or_create_folder(
                name=timestamp,
                parent_id=user_folder_id,
                mime_type="application/vnd.google-apps.folder"
            )

            if not session_folder_id:
                raise RuntimeError("Failed to create session folder")

            return session_folder_id

        except Exception as e:
            logger.error(f"Folder creation failed: {str(e)}")
            raise

    async def _get_or_create_folder(self, name: str, parent_id: str = None, mime_type: str = None) -> str:
        """Поиск или создание папки"""
        try:
            # Проверка подключения
            if not self.session:
                raise RuntimeError("Not connected to Google Drive")

            # Поиск существующей папки
            query = f"name='{name}' and trashed=false"
            if parent_id:
                query += f" and '{parent_id}' in parents"
            if mime_type:
                query += f" and mimeType='{mime_type}'"

            async with self.session.get(
                    "https://www.googleapis.com/drive/v3/files",
                    params={"q": query},
                    headers={"Authorization": f"Bearer {self.credentials.token}"}
            ) as resp:
                if resp.status != 200:
                    error = await resp.text()
                    raise Exception(f"Search failed: {error}")

                result = await resp.json()
                if result.get('files'):
                    return result['files'][0]['id']

            # Создание новой папки
            metadata = {
                "name": name,
                "mimeType": mime_type,
                "parents": [parent_id] if parent_id else []
            }

            async with self.session.post(
                    "https://www.googleapis.com/drive/v3/files",
                    json=metadata,
                    headers={"Authorization": f"Bearer {self.credentials.token}"}
            ) as resp:
                if resp.status != 200:
                    error = await resp.text()
                    raise Exception(f"Creation failed: {error}")

                result = await resp.json()
                return result['id']

        except Exception as e:
            logger.error(f"Folder operation failed: {str(e)}")
            raise

    async def upload_photo(self, folder_id: str, file_name: str, content: bytes):
        """Загрузка фото"""
        try:
            # Проверка подключения
            if not self.session:
                raise RuntimeError("Not connected to Google Drive")

            metadata = {
                "name": file_name,
                "parents": [folder_id]
            }

            form = aiohttp.FormData()
            form.add_field('metadata',
                           json.dumps(metadata),
                           content_type='application/json')
            form.add_field('file',
                           content,
                           filename=file_name,
                           content_type='image/jpeg')

            async with self.session.post(
                    "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart",
                    data=form,
                    headers={"Authorization": f"Bearer {self.credentials.token}"}
            ) as resp:
                if resp.status != 200:
                    error = await resp.text()
                    raise Exception(f"Upload failed: {error}")

                return await resp.json()

        except Exception as e:
            logger.error(f"Upload failed: {str(e)}")
            raise

    async def close(self):
        """Закрытие соединения"""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("Google Drive connection closed")