import aio_pika
import json
import logging
from datetime import datetime
from .db_init import create_tables, get_connection
from .config import settings

logger = logging.getLogger(__name__)


async def process_logs_batch(logs_batch: list):
    try:
        async with get_connection() as conn:
            records = [
                (
                    datetime.fromisoformat(log["time"]),
                    log["level"],
                    log["message"],
                    log.get("user_id")
                )
                for log in logs_batch
            ]

            await conn.executemany('''
                INSERT INTO logs(time, level, message, user_id)
                VALUES($1, $2, $3, $4)
            ''', records)
            logger.info(f"Inserted {len(records)} logs")

    except Exception as e:
        logger.error(f"Error processing batch: {str(e)}")
        raise


async def consume_logs():
    try:
        await create_tables()
        logger.info("Starting log consumer...")

        connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
        async with connection:
            channel = await connection.channel()
            queue = await channel.declare_queue("logs_queue", durable=True)

            logger.info("Waiting for logs...")
            async for message in queue:
                async with message.process():
                    try:
                        logs_batch = json.loads(message.body.decode())
                        if isinstance(logs_batch, list):
                            await process_logs_batch(logs_batch)
                            logger.debug("Batch processed successfully")
                    except Exception as e:
                        logger.error(f"Message processing error: {str(e)}")

    except Exception as e:
        logger.critical(f"Log consumer failed: {str(e)}")
        raise