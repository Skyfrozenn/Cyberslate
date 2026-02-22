from fastapi import Depends

import redis.asyncio as redis

from app.models import UserModel
from app.config import SECRET_KEY, ACCES_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS, ALGORITHM
from app.schemas.users import RefreshToken, RefreshTokenlist
from app.services.redis_client import get_redis

import jwt

from datetime import datetime, timedelta,timezone



class JWTManager:
    def __init__(self, algorithm, secret_key, acces_token_expire_minutes, refresh_token_expire_days) :
        self.algorithm = algorithm
        self.__secret_key = secret_key
        self.acces_token_expire_minutes = acces_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days

    def create_access_token(self, data : dict):
        to_encody = data.copy()
        exprire = datetime.now(timezone.utc) + timedelta(minutes=self.acces_token_expire_minutes)
        to_encody.update(
            {
            "exp" : exprire,
            "token_types" : "access"
        }
        )
        return jwt.encode(to_encody, self.__secret_key, algorithm = self.algorithm)



    def create_refresh_token(self, data : dict):
        to_encody = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(days = self.refresh_token_expire_days)
        to_encody.update(
            {
            "exp" : expire,
            "token_types" : "refresh"
            }
        )
        refresh_token = jwt.encode(to_encody, self.__secret_key, algorithm = self.algorithm)
        return refresh_token



    async def new_access_token(self, user : UserModel):
        data = {
        "sub" : user.email,
        "role" : user.role,
        "id" : user.id
        }
        return self.create_access_token(data)



    async def new_refresh_token(self, user : UserModel):
        data = {
        "sub" : user.email,
        "role" : user.role,
        "id" : user.id
        }
        return self.create_refresh_token(data)
    

    async def revoke_refresh_tokens(self, tokens : RefreshTokenlist, r : redis.Redis = Depends(get_redis)):
        for token_obj in tokens.refresh_tokens:
            await r.set(f"blacklist:{token_obj.refresh_token}", "revoked", ex = self.refresh_token_expire_days * 24 * 60 * 60)
        return {"detail" : "Токены отозваны!"}


#создание обьекта
jwt_manager = JWTManager(
    secret_key=SECRET_KEY,
    algorithm = ALGORITHM,
    acces_token_expire_minutes=ACCES_TOKEN_EXPIRE_MINUTES,
    refresh_token_expire_days=REFRESH_TOKEN_EXPIRE_DAYS
)
