import json
import base64
import asyncio
import aio_pika
import numpy as np
import cv2
import logging
from os import getenv

# Импортируем функцию обработки фотографий
from .pipe import pipeline_caries

logger = logging.getLogger(__name__)

RABBITMQ_URL = getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq/")

def decode_image_from_b64(image_b64: str) -> np.ndarray:
    """
    Декодирует строку base64 в numpy-массив (изображение)
    """
    image_bytes = base64.b64decode(image_b64)
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return img

def encode_image_to_b64(image: np.ndarray) -> str:
    """
    Кодирует numpy-массив (изображение) в base64 строку (JPEG)
    """
    ret, buffer = cv2.imencode('.jpg', image)
    if not ret:
        raise ValueError("Ошибка кодирования изображения")
    return base64.b64encode(buffer).decode("utf-8")

async def on_request(message: aio_pika.IncomingMessage, channel):
    """
    Колбэк для обработки входящих сообщений из очереди.
    """
    async with message.process():
        try:
            payload = json.loads(message.body.decode())
            photos_b64 = payload.get("photos", [])
            # Преобразуем base64-строки в изображения
            images = [decode_image_from_b64(photo) for photo in photos_b64]
            error, result_list, result_dict = pipeline_caries(images)
            if error is None:
                # Кодируем обработанные изображения обратно в base64
                result_list_encoded = [encode_image_to_b64(img) for img in result_list]
            else:
                result_list_encoded = []
        except Exception as e:
            error = str(e)
            result_list_encoded = []
            result_dict = {}
        response = {
            "error": error,
            "result_list": result_list_encoded,
            "result_dict": result_dict,
        }
        logger.info(f"Отправляем ответ: {response}")
        if message.reply_to:
            # Используем default exchange напрямую
            await channel.default_exchange.publish(
                aio_pika.Message(
                    body=json.dumps(response).encode(),
                    correlation_id=message.correlation_id,
                ),
                routing_key=message.reply_to,
            )

async def main():
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    async with connection:
        channel = await connection.channel()
        queue = await channel.declare_queue("photo_processing")
        try:
            # Передаем channel в on_request
            await queue.consume(lambda message: on_request(message, channel))
            logger.info(" [*] Ожидаю заданий в очереди 'photo_processing'. Для выхода нажмите CTRL+C")
            await asyncio.Future()  # Бесконечное ожидание
        except Exception as e:
            logger.error(f"Ошибка в основном цикле: {e}")
            # Закрываем канал и пересоздаём его при необходимости
            await channel.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())