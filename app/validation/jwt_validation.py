import jwt
import redis.asyncio as redis

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from sqlalchemy import select

from app.database import  AsyncSession
from app.models.users import UserModel
from app.db_depends import get_async_db
from app.services.redis_client import get_redis
from app.schemas.users import RefreshToken

from app.config import ALGORITHM, SECRET_KEY



oath2_scheme = OAuth2PasswordBearer(tokenUrl="users/token")


class JWTValidator:
    def __init__(self, secret_key: str, algorithm: str):
        self.__secret_key = secret_key
        self.__algorithm = algorithm

    async def get_current_user(
        self,
        token: str = Depends(oath2_scheme),
        db: AsyncSession = Depends(get_async_db)
    ) -> UserModel:
        """
        Функция охранник проверяет access токен
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Не удалось подтвердить учетные данные!",
            headers={"WWW-Authenticate": "Bearer"}
        )
        try:
            payload = jwt.decode(token, self.__secret_key, algorithms=[self.__algorithm])
            email: str | None = payload.get("sub")
            token_types: str | None = payload.get("token_types")
            if email is None or token_types != "access":
                raise credentials_exception
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Время токена истекло!",
                headers={"WWW-Authenticate": "Bearer"}
            )
        except jwt.PyJWTError:
            raise credentials_exception

        request_user = await db.scalars(
            select(UserModel)
            .where(UserModel.email == email, UserModel.is_active == True)
        )
        user = request_user.first()
        if user is None:
            raise credentials_exception
        return user



    async def validate_refresh_token(
        self,
        token: RefreshToken,
        db: AsyncSession = Depends(get_async_db),
        r: redis.Redis = Depends(get_redis)
    ) -> UserModel:
        """
        Валидация refresh токена с проверкой на blacklist
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Не удалось подтвердить учетные данные!",
            headers={"WWW-Authenticate": "Bearer"}
        )

        # Проверка на blacklist
        if await r.get(f"blacklist:{token.refresh_token}") is not None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Токен был отозван!",
                headers={"WWW-Authenticate": "Bearer"}
            )
        try:
            payload = jwt.decode(token.refresh_token, self.__secret_key, algorithms=[self.__algorithm])
            email: str | None = payload.get("sub")
            token_types: str | None = payload.get("token_types")
            if email is None or token_types != "refresh":
                raise credentials_exception
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Время токена истекло!",
                headers={"WWW-Authenticate": "Bearer"}
            )
        except jwt.PyJWTError:
            raise credentials_exception

        request_user = await db.scalars(
            select(UserModel)
            .where(UserModel.email == email, UserModel.is_active == True)
        )
        user = request_user.first()
        if user is None:
            raise credentials_exception
        return user



#создание обьекта
jwt_validator = JWTValidator(
    secret_key=SECRET_KEY,
    algorithm=ALGORITHM
)
