from loguru import logger

from os import getenv
from dotenv import load_dotenv


load_dotenv()

#JWT - НАСТРОЙКА
SECRET_KEY = getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCES_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7



#файл логирования
logger.add("info.log", format="Log: [{extra[log_id]}:{time} - {level} - {message}]", level="INFO", enqueue = True)