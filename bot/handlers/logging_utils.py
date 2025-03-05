import asyncio
from datetime import datetime
from aiogram import types
from ..queue.rabbitmq_client import send_logs_batch

class LogBuffer:
    def __init__(self, interval=60):
        self.buffer = []
        self.interval = interval  # В секундах
        self.lock = asyncio.Lock()
        self.task = None

    async def add_log(self, level: str, message: str, user_id: int = None):
        async with self.lock:
            self.buffer.append({
                "time": datetime.utcnow(),
                "level": level,
                "message": message,
                "user_id": user_id
            })

    async def start_periodic_send(self):
        while True:
            await asyncio.sleep(self.interval)
            await self.flush()

    async def flush(self):
        async with self.lock:
            if self.buffer:
                try:
                    await send_logs_batch(self.buffer.copy())
                    self.buffer.clear()
                except Exception as e:
                    print(f"Error sending logs: {str(e)}")


# Инициализация буфера с интервалом 60 секунд (1 минута)
log_buffer = LogBuffer(interval=60)


async def log_event(level: str, message: str, user_id: int = None):
    await log_buffer.add_log(level, message, user_id)


async def start_log_scheduler():
    log_buffer.task = asyncio.create_task(log_buffer.start_periodic_send())