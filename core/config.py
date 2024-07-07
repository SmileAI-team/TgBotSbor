from pathlib import Path
from pydantic_settings import BaseSettings
import os


BASE_DIR = Path(__file__).parent.parent


class Settings(BaseSettings):
    db_url: str = f"sqlite+aiosqlite:///{BASE_DIR}/db.sqlite3"
    db_echo: bool = True
    google_drive_parent_folder_id: str = "1GPxeo8XUaT9z_gVF3liuDqni-jdySbHj"
    MAX_FILE_SIZE_MB: int = 30
    MAX_FILE_SIZE: int = MAX_FILE_SIZE_MB * 1024 * 1024  # байт

settings = Settings()
