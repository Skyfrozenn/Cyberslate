from contextlib import asynccontextmanager
from time import sleep

from fastapi import FastAPI
import redis.asyncio as redis

from dotenv import load_dotenv
from os import getenv

load_dotenv()

redis_client: redis.Redis | None = None


async def get_redis() -> redis.Redis:
    global redis_client
    if not redis_client:
        # Используем REDIS_URL из .env через settings
        redis_client = redis.from_url(
            getenv("REDIS_URL"),
            decode_responses=True
        )
    return redis_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Приложение запускается...")
    
    # Попытки подключения к Redis (5 попыток с интервалом 2 секунды)
    max_retries = 5
    retry_delay = 2
    
    for attempt in range(1, max_retries + 1):
        try:
            redis_client = await get_redis()
            await redis_client.ping()
            print("✅ Redis подключён!")
            break
        except Exception as e:
            print(f"❌ Попытка {attempt}/{max_retries}: Ошибка подключения к Redis: {e}")
            if attempt < max_retries:
                print(f"⏳ Повторная попытка через {retry_delay} сек...")
                sleep(retry_delay)
            else:
                print(f"❌ Не удалось подключиться к Redis после {max_retries} попыток")
                print("⚠️ Приложение запускается без подключения к Redis!")
    yield 
    print("🛑 Приложение останавливается...")
    try:
        from app.services.redis_client import redis_client
        if redis_client:
            await redis_client.close()
            print("✅ Redis соединение закрыто")
    except Exception as e:
        print(f"❌ Ошибка закрытия Redis: {e}")