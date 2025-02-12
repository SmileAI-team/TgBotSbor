import json
import uuid
import asyncio
import aio_pika
import logging
from os import getenv

logger = logging.getLogger(__name__)

# Получаем URL RabbitMQ из переменных окружения или используем значение по умолчанию
RABBITMQ_URL = getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq/")


async def rpc_call(payload: dict, timeout: int = 30) -> dict:
    """
    Отправляет payload в очередь 'photo_processing' и ждёт ответа по RPC.
    :param payload: Словарь с данными (например, {"user_id": ..., "photos": [<b64>, ...]})
    :param timeout: Время ожидания ответа (секунд)
    :return: Ответ в виде словаря
    """
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    async with connection:
        channel = await connection.channel()
        # Создаем временную очередь для ответов
        callback_queue = await channel.declare_queue(exclusive=True)
        correlation_id = str(uuid.uuid4())
        future = asyncio.get_event_loop().create_future()

        async def on_response(message: aio_pika.IncomingMessage):
            async with message.process():
                if message.correlation_id == correlation_id:
                    future.set_result(message.body.decode())

        await callback_queue.consume(on_response)

        try:
            # Отправляем сообщение в очередь "photo_processing"
            await channel.default_exchange.publish(
                aio_pika.Message(
                    body=json.dumps(payload).encode(),
                    correlation_id=correlation_id,
                    reply_to=callback_queue.name,
                ),
                routing_key="photo_processing",
            )
            # Ждём ответа
            response = await asyncio.wait_for(future, timeout=timeout)
            logger.info(f"Получен ответ по correlation_id={correlation_id}")
            return json.loads(response)
        except asyncio.TimeoutError:
            logger.error("Timeout при ожидании ответа от RabbitMQ")
            raise Exception("Timeout при ожидании ответа от RabbitMQ")
        except Exception as e:
            logger.error(f"Ошибка при взаимодействии с RabbitMQ: {e}")
            raise
