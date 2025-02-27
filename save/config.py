import os
from pathlib import Path

class Settings:
    GOOGLE_CREDS_FILE = str(Path(__file__).parent / "smile-ai-bot-1dccd401d6ed.json")
    RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://admin:admin@rabbitmq:5672/")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "save_module.log")

    @classmethod
    def check_credentials(cls):
        if not Path(cls.GOOGLE_CREDS_FILE).exists():
            raise FileNotFoundError(f"Credentials not found at: {cls.GOOGLE_CREDS_FILE}")

settings = Settings()