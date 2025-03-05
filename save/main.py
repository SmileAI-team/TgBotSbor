import asyncio
import logging
import json
import aio_pika
from .db_init import create_tables
from .log_consumer import consume_logs
from .google_drive_client import GoogleDriveClient
from .queue_handler import SaveQueueHandler
from .config import settings

logger = logging.getLogger(__name__)


async def main():
    try:
        # Инициализация клиента Google Drive
        drive_client = GoogleDriveClient(settings.GOOGLE_CREDS_FILE)
        handler = SaveQueueHandler(drive_client)
        await drive_client.connect()

        # Инициализация БД
        await create_tables()

        # Запуск потребителя логов в фоне
        log_consumer_task = asyncio.create_task(consume_logs())

        # Подключение к RabbitMQ для основного функционала
        connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
        async with connection:
            channel = await connection.channel()
            queue = await channel.declare_queue("save_photos", durable=True)

            # Обработка сообщений
            async for message in queue:
                try:
                    data = json.loads(message.body.decode())
                    success = await handler.process_message(data)
                    if success:
                        await message.ack()
                    else:
                        await message.nack()
                except Exception as e:
                    logger.error(f"Message processing error: {str(e)}")
                    await message.reject()

    except Exception as e:
        logger.critical(f"Critical error: {str(e)}")
    finally:
        await drive_client.close()
        log_consumer_task.cancel()
        try:
            await log_consumer_task
        except asyncio.CancelledError:
            pass


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('save_module.log')
        ]
    )
    asyncio.run(main())