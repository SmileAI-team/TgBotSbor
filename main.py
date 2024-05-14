from contextlib import asynccontextmanager

from fastapi import FastAPI

import uvicorn

from core.config import settings
from core.models import Base, db_helper
from user.views import router as user_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with db_helper.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield


app = FastAPI(lifespan=lifespan)
app.include_router(router=user_router)


@app.get("/")
def hello_index():
    return {
        "message": "Hello index!",
    }


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
