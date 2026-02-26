from fastapi import FastAPI

from contextlib import asynccontextmanager
from fastapi import Request
import redis.asyncio as redis
from dotenv import load_dotenv
from os import getenv
import asyncio

load_dotenv()


async def get_redis(request: Request) -> redis.Redis:
    """
    Получает Redis-подключение из app.state.
    Подключение создаётся 1 раз при старте приложения.
    """
    return request.app.state.redis_client


@asynccontextmanager
async def lifespan(app : FastAPI):
    print("🚀 Приложение запускается...")

    # Создаём подключение 1 раз при старте
    app.state.redis_client = redis.from_url(
        getenv("REDIS_URL"),
        decode_responses=True
    )

    # Проверяем подключение (5 попыток с интервалом 2 секунды)
    max_retries = 5
    retry_delay = 2

    for attempt in range(1, max_retries + 1):
        try:
            await app.state.redis_client.ping()
            print("✅ Redis подключён!")
            break
        except Exception as e:
            print(f"❌ Попытка {attempt}/{max_retries}: Ошибка подключения к Redis: {e}")
            if attempt < max_retries:
                print(f"⏳ Повторная попытка через {retry_delay} сек...")
                await asyncio.sleep(retry_delay)
            else:
                print(f"❌ Не удалось подключиться к Redis после {max_retries} попыток")
                print("⚠️ Приложение запускается без подключения к Redis!")

    yield

    print("🛑 Приложение останавливается...")
    try:
        await app.state.redis_client.close()
        print("✅ Redis соединение закрыто")
    except Exception as e:
        print(f"❌ Ошибка закрытия Redis: {e}")