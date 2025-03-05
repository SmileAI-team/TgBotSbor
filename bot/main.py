import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand
from bot.config_data.config import Config, load_config
# Импортируем роутеры
from bot.handlers.user_handlers import *
from bot.handlers.user_handlers import router as user_handlers_router
# Импортируем миддлвари
from bot.middlewares.custom_logging import CustomLoggingMiddleware
# Импортируем логирование
from .handlers.logging_utils import start_log_scheduler
# Импортируем вспомогательные функции для создания нужных объектов
# ...
#from keyboards.main_menu import set_main_menu

# Инициализируем логгер
logger = logging.getLogger(__name__)

async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="/start", description="Запустить бота"),
    ]
    await bot.set_my_commands(commands)

# Функция конфигурирования и запуска бота
async def main():
    # Конфигурируем логирование
    logging.basicConfig(
        level=logging.INFO,
        format='%(filename)s:%(lineno)d #%(levelname)-8s '
               '[%(asctime)s] - %(name)s - %(message)s')

    # Выводим в консоль информацию о начале запуска бота
    logger.info('Starting bot')

    # Загружаем конфиг в переменную config
    config: Config = load_config()

    # Инициализируем объект хранилища
    #storage = ...

    # Инициализируем бот и диспетчер
    bot = Bot(
        token=config.tg_bot.token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    # Инициализируем другие объекты (пул соединений с БД, кеш и т.п.)
    # ...

    # Помещаем нужные объекты в workflow_data диспетчера
    # dp.workflow_data.update(...)
    logger.info('Подключаем логирование')
    await start_log_scheduler()
    # Настраиваем главное меню бота
    #await set_main_menu(bot)

    # Регистриуем роутеры
    logger.info('Подключаем роутеры')
    dp.include_router(user_handlers_router)

    # Регистрируем миддлвари
    logger.info('Подключаем миддлвари')
    dp.message.middleware(CustomLoggingMiddleware())

    # Пропускаем накопившиеся апдейты и запускаем polling
    #await bot.delete_webhook(drop_pending_updates=True)
    await set_commands(bot)
    await dp.start_polling(bot)


asyncio.run(main())