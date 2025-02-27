import json
import base64
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class SaveQueueHandler:
    def __init__(self, drive_client):
        self.drive_client = drive_client
        logger.info("Queue handler initialized")

    async def process_message(self, message: dict):
        try:
            # Проверка структуры сообщения
            if not isinstance(message, dict):
                raise ValueError("Invalid message format")

            user_id = message.get('user_id')
            photos = message.get('photos', [])

            # Валидация
            if not user_id or not isinstance(photos, list):
                raise ValueError("Invalid message content")

            logger.info(f"Processing {len(photos)} photos for user {user_id}")

            # Создаем структуру папок
            folder_id = await self.drive_client.create_folder_structure(user_id)

            # Загружаем фото
            for idx, photo_b64 in enumerate(photos):
                try:
                    content = base64.b64decode(photo_b64)
                    file_name = f"photo_{idx + 1}.jpg"
                    await self.drive_client.upload_photo(folder_id, file_name, content)
                except Exception as e:
                    logger.error(f"Error uploading photo {idx}: {str(e)}")
                    continue

            return True

        except Exception as e:
            logger.error(f"Processing failed: {str(e)}")
            return False