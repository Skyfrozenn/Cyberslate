from fastapi import FastAPI, Request

from fastapi.responses import JSONResponse

from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.services.redis_client import lifespan
from app.routers import users

from time import time, sleep
from uuid import uuid4


from app.config import logger


 


 


app = FastAPI(
    title="Проект для турниров по киберспорту",
    version="1.0",
    lifespan=lifespan
)


@app.middleware("http")
async def log_middleware(request: Request, call_next):
    log_id = str(uuid4())
    with logger.contextualize(log_id=log_id):
        try:
            response = await call_next(request) #передаем дальше поток, чтобы получить request данные
            if response.status_code in [401, 402, 403, 404]:
                logger.warning(f"Ошибка запроса к  {request.url.path} failed")
            else:
                logger.info('Успешный запрос к ' + request.url.path)
        except Exception as ex:
            logger.error(f"Ошибка запроса к  {request.url.path} failed: {ex}")
            response = JSONResponse(content={"success": False}, status_code=500)
        return response



app.add_middleware( #4
    GZipMiddleware,
    minimum_size = 1000,
    compresslevel=5
)

@app.middleware("http") #3
async def modify_request_response_middleware(request: Request, call_next):
    start_time = time() #текущее время
    response = await call_next(request) #некст мидлвар или приложение
    duration = time() - start_time #смотрим время
    logger.info(f"Время выполнения запроса к : {duration:.10f} seconds | {request.method} {request.url.path}") #логирование
    return response  #возврат запроса


app.add_middleware( #2
    TrustedHostMiddleware,
    allowed_hosts = ["localhost", "127.0.0.1"] #разрешенные хосты
)

# app.add_middleware(HTTPSRedirectMiddleware) РЕДИРЕКТ НА https 

app.add_middleware( #1
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",           
        "http://localhost:5173",           
    ],
    allow_credentials=True,  
    allow_methods=["*"],  
    allow_headers=["Authorization", "Content-Type"] 
)



app.include_router(users.router)


@app.get("/")
async def home_page() -> dict:
    return {"message" : "hello"}