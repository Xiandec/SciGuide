"""Основной файл приложения FastAPI."""

from contextlib import asynccontextmanager

import asyncpg
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from redis.asyncio import Redis

from config import settings
from shared.presentation.api.router import api_router


@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    """
    Управляет жизненным циклом приложения.
    Создает пулы соединений с БД при старте и закрывает их при остановке.
    """
    app_instance.state.db_pool = await asyncpg.create_pool(
        user=settings.db_user,
        password=settings.db_password,
        database=settings.db_name,
        host=settings.db_host,
        port=settings.db_port,
    )

    redis_client = Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        db=settings.redis_db,
        password=settings.redis_password,
    )
    app_instance.state.redis = redis_client

    try:
        yield
    finally:
        await app_instance.state.db_pool.close()
        await redis_client.close()


app = FastAPI(
    title="SciGuide Backend",
    description="Сервис для автоматической справочной системы на основе языковых моделей для выбранного научного направления",
    version="0.0.0",
    debug=settings.debug,
    lifespan=lifespan,
)

# Автоматически добавляет метрики HTTP запросов
Instrumentator().instrument(app).expose(app)

# Подключение маршрутов
app.include_router(api_router)


@app.get("/health")
async def health_check():
    """Проверка состояния сервиса"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.host, port=settings.port)
