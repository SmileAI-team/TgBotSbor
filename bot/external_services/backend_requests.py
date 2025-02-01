import httpx
import logging
from typing import List, Dict, Any, Tuple
from bot.config_data.config import Config, load_config

# Загружаем конфиг в переменную config
config: Config = load_config()
API_BASE_URL = config.api_url
logger = logging.getLogger(__name__)

# Настраиваем логгер
logging.basicConfig(
    level=logging.INFO,
    format='%(filename)s:%(lineno)d #%(levelname)-8s '
           '[%(asctime)s] - %(name)s - %(message)s')

# Асинхронная функция для получения списка пользователей
async def fetch_users() -> List[Dict[str, Any]]:
    async with httpx.AsyncClient() as client:
        logger.info(f"Fetching users from {API_BASE_URL}/users/list")
        response = await client.get(f'{API_BASE_URL}/users/list')
        logger.info(f"Received response {response.status_code}: {response.json()}")
        return response.json()

# Создание пользователя
async def create_user(telegram_id: str, card_number: str, google_path: str) -> Dict[str, Any]:
    async with httpx.AsyncClient() as client:
        payload = {
            "telegram_id": telegram_id,
            "card_number": card_number,
            "google_path": google_path
        }
        logger.info(f"Sending request to {API_BASE_URL}/users/ with payload {payload}")
        response = await client.post(f'{API_BASE_URL}/users/', json=payload)
        logger.info(f"Received response {response.status_code}: {response.json()}")
        return response.json()

# Получение пользователя
async def get_user(user_id: int) -> Dict[str, Any]:
    async with httpx.AsyncClient() as client:
        logger.info(f"Fetching user {user_id} from {API_BASE_URL}/users/{user_id}/")
        response = await client.get(f'{API_BASE_URL}/users/{user_id}/')
        logger.info(f"Received response {response.status_code}: {response.json()}")
        return response.json()

# Обновление пользователя
async def update_user(user_id: int, telegram_id: str, card_number: str, google_path: str) -> Dict[str, Any]:
    async with httpx.AsyncClient() as client:
        payload = {
            "telegram_id": telegram_id,
            "card_number": card_number,
            "google_path": google_path
        }
        logger.info(f"Updating user {user_id} with payload {payload}")
        response = await client.put(f'{API_BASE_URL}/users/{user_id}/', json=payload)
        logger.info(f"Received response {response.status_code}: {response.json()}")
        return response.json()

# Удаление пользователя
async def delete_user(user_id: int) -> None:
    async with httpx.AsyncClient() as client:
        logger.info(f"Deleting user {user_id} from {API_BASE_URL}/users/{user_id}/")
        response = await client.delete(f'{API_BASE_URL}/users/{user_id}/')
        logger.info(f"Received response {response.status_code}: {response.text}")
        return response.text

# Создание пользователя по telegram_id
async def create_user_by_telegram(telegram_id: str) -> httpx.Response:
    async with httpx.AsyncClient() as client:
        params = {"telegram_id": telegram_id}
        logger.info(f"Sending request to {API_BASE_URL}/users/telegram/ with params {params}")
        response = await client.post(f'{API_BASE_URL}/users/telegram/', params=params)
        logger.info(f"Received response {response.status_code}: {response.json()}")
        return response

# Получение пользователя по telegram_id
async def fetch_items() -> List[Dict[str, Any]]:
    async with httpx.AsyncClient() as client:
        logger.info(f"Fetching items from {API_BASE_URL}/items/list")
        response = await client.get(f'{API_BASE_URL}/items/list')
        logger.info(f"Received response {response.status_code}: {response.json()}")
        return response.json()

# Создание элемента
async def create_item(user_id: int, time: str, google_drive_path: str, viewed: bool, validated: bool, comment: str) -> Dict[str, Any]:
    async with httpx.AsyncClient() as client:
        payload = {
            "user_id": user_id,
            "time": time,
            "google_drive_path": google_drive_path,
            "viewed": viewed,
            "validated": validated,
            "comment": comment
        }
        logger.info(f"Creating item with payload {payload}")
        response = await client.post(f'{API_BASE_URL}/items/', json=payload)
        logger.info(f"Received response {response.status_code}: {response.json()}")
        return response.json()

# Получение элемента
async def get_item(item_id: int) -> Dict[str, Any]:
    async with httpx.AsyncClient() as client:
        logger.info(f"Fetching item {item_id} from {API_BASE_URL}/items/{item_id}/")
        response = await client.get(f'{API_BASE_URL}/items/{item_id}/')
        logger.info(f"Received response {response.status_code}: {response.json()}")
        return response.json()

# Обновление элемента
async def update_item(item_id: int, user_id: int, time: str, google_drive_path: str, viewed: bool, validated: bool, comment: str) -> Dict[str, Any]:
    async with httpx.AsyncClient() as client:
        payload = {
            "user_id": user_id,
            "time": time,
            "google_drive_path": google_drive_path,
            "viewed": viewed,
            "validated": validated,
            "comment": comment
        }
        logger.info(f"Updating item {item_id} with payload {payload}")
        response = await client.put(f'{API_BASE_URL}/items/{item_id}/', json=payload)
        logger.info(f"Received response {response.status_code}: {response.json()}")
        return response.json()

# Удаление элемента
async def delete_item(item_id: int) -> None:
    async with httpx.AsyncClient() as client:
        logger.info(f"Deleting item {item_id} from {API_BASE_URL}/items/{item_id}/")
        response = await client.delete(f'{API_BASE_URL}/items/{item_id}/')
        logger.info(f"Received response {response.status_code}: {response.text}")
        return response.text

# Загрузка файлов
async def upload_files(telegram_id: str, files: List[Tuple[str, bytes]], comment: str) -> dict:
    timeout = httpx.Timeout(10.0, read=None)
    async with httpx.AsyncClient(timeout=timeout) as client:
        files_data = [('files', (file[0], file[1], 'image/jpeg')) for file in files]
        data = {
            'telegram_id': telegram_id,
            'comment': comment
        }
        logger.info(f"Uploading files for telegram_id {telegram_id} with comment: {comment} in upload_files body")
        try:
            response = await client.post(f'{API_BASE_URL}/items/upload/', files=files_data, data=data)
            logger.info(f"Request URL: {response.request.url}")
            logger.info(f"Request headers: {response.request.headers}")
            logger.info(f"Request files data: {files_data}")
            logger.info(f"Request data: {data}")
            logger.info(f"Received response {response.status_code}: {response.text}")

            if response.status_code == 200:
                return response.json()  # Парсим JSON-ответ в словарь
            else:
                raise httpx.HTTPStatusError(f"Unexpected status code: {response.status_code}", request=response.request, response=response)

        except httpx.HTTPStatusError as exc:
            logger.error(f"HTTP error occurred: {exc.response.status_code} - {exc.response.text}")
            raise
        except httpx.ReadTimeout as exc:
            logger.error(f"HTTPX ReadTimeout occurred: {exc}")
            raise
        except Exception as exc:
            logger.error(f"An error occurred: {str(exc)}")
            raise