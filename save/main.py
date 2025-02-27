import aio_pika
import json
import logging
import asyncio
from .queue_handler import SaveQueueHandler
from .google_drive_client import GoogleDriveClient
from .config import settings

logger = logging.getLogger(__name__)


async def main():
    try:
        # Инициализация
        drive_client = GoogleDriveClient(settings.GOOGLE_CREDS_FILE)
        handler = SaveQueueHandler(drive_client)
        await drive_client.connect()

        # Подключение к RabbitMQ
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