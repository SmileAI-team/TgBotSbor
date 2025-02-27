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

RABBITMQ_URL = getenv("RABBITMQ_URL", "amqp://admin:admin@rabbitmq:5672/")


def decode_image_from_b64(image_b64: str) -> np.ndarray:
    """
    Декодирует строку base64 в numpy-массив (изображение)
    с расширенным логированием для диагностики
    """
    logger.debug(f"Начало декодирования. Тип данных: {type(image_b64)}, длина: {len(image_b64)}")
    logger.debug(f"Первые 50 символов: {image_b64[:50]}")

    try:
        # Очистка данных
        cleaned_b64 = image_b64.strip().split(",")[-1]
        cleaned_b64 = cleaned_b64.replace(" ", "+")
        logger.debug(f"После очистки. Длина: {len(cleaned_b64)}, первые 30 символов: {cleaned_b64[:30]}...")

        # Проверка валидных символов
        valid_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=")
        invalid_chars = [c for c in cleaned_b64 if c not in valid_chars]
        if invalid_chars:
            logger.warning(f"Обнаружены недопустимые символы: {invalid_chars[:5]}... (всего {len(invalid_chars)})")

        # Добавление паддинга
        original_length = len(cleaned_b64)
        missing_padding = original_length % 4
        if missing_padding:
            logger.debug(f"Добавляем паддинг: недостает {4 - missing_padding} символов")
            cleaned_b64 += "=" * (4 - missing_padding)

        logger.debug(f"После паддинга. Длина: {len(cleaned_b64)}, последние 4 символа: {cleaned_b64[-4:]}")

        # Декодирование
        image_bytes = base64.b64decode(cleaned_b64, validate=True)
        logger.debug(f"Успешно декодировано. Размер бинарных данных: {len(image_bytes)} байт")

        # Преобразование в изображение
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            logger.error("Ошибка декодирования бинарных данных в изображение")
            raise ValueError("Не удалось декодировать бинарные данные в изображение")

        logger.info(f"Успешно декодировано изображение. Размер: {img.shape[1]}x{img.shape[0]}")
        return img

    except Exception as e:
        logger.error(f"Критическая ошибка декодирования: {str(e)}")
        logger.error(f"Очищенные данные для отладки (первые 100 символов): {cleaned_b64[:100]}")
        raise


def encode_image_to_b64(image: np.ndarray) -> str:
    ret, buffer = cv2.imencode('.jpg', image)
    if not ret:
        raise ValueError("Ошибка кодирования изображения")

    # Кодируем БЕЗ удаления паддинга
    encoded = base64.b64encode(buffer).decode("utf-8")
    logger.debug(f"Закодировано изображение. Длина: {len(encoded)}, паддинг: {encoded[-4:]}")
    return encoded


async def on_request(message: aio_pika.IncomingMessage, channel):
    """
    Колбэк для обработки входящих сообщений из очереди.
    """
    async with message.process():
        # Инициализируем переменные значениями по умолчанию
        response = {
            "mouth_type": [],
            "result_list": [],
            "result_dict": {}
        }

        try:
            payload = json.loads(message.body.decode())
            photos_b64 = payload.get("photos", [])

            if not photos_b64:
                logger.warning("Получен запрос без фотографий")
                return

            # Фильтруем некорректные фото (None и пустые строки)
            valid_photos = [p for p in photos_b64 if p is not None and p.strip()]

            images = []
            for photo in valid_photos:
                try:
                    images.append(decode_image_from_b64(photo))
                except Exception as e:
                    logger.error(f"Ошибка декодирования фото: {str(e)}")
                    continue

            # Получаем результаты обработки
            mouth_type, result_list, result_dict = pipeline_caries(images)

            # Фильтруем None в result_list перед кодированием
            result_list_encoded = [
                encode_image_to_b64(img)
                for img in result_list
                if img is not None
            ]

            response.update({
                "mouth_type": mouth_type,
                "result_list": result_list_encoded,
                "result_dict": result_dict
            })

        except Exception as e:
            logger.error(f"Критическая ошибка обработки: {str(e)}", exc_info=True)
            response.update({
                "mouth_type": [],
                "result_list": [],
                "result_dict": {}
            })

        # Отправляем ответ
        if message.reply_to:
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