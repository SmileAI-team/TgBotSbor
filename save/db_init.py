import asyncpg
import logging
from contextlib import asynccontextmanager
from .config import settings

logger = logging.getLogger(__name__)

async def create_tables():
    try:
        conn = await asyncpg.connect(settings.DB_URL)
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id SERIAL PRIMARY KEY,
                time TIMESTAMP NOT NULL,
                level VARCHAR(20) NOT NULL,
                message TEXT NOT NULL,
                user_id BIGINT
            )
        ''')
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating tables: {str(e)}")
        raise
    finally:
        await conn.close()

@asynccontextmanager
async def get_connection():
    conn = await asyncpg.connect(settings.DB_URL)
    try:
        yield conn
    finally:
        await conn.close()