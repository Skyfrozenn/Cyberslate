 
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

import redis.asyncio as redis

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.users import UserCreateSchema, UserResponseSchema, VerifyCode, ResendCodeSchema
 
from app.models.users import UserModel
from app.db_depends import get_async_db

from app.services.redis_client import get_redis
from app.services.email import send_verification_email

from app.validation.hash_password import hash_password, verify_password
from app.validation.jwt_manager import jwt_manager
from app.validation.jwt_validation import jwt_validator

import random

router = APIRouter(
    prefix="/users",
    tags=["USERS"]
)


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreateSchema,
    db: AsyncSession = Depends(get_async_db),
    redis_client = Depends(get_redis)
):
    existing_user = await db.scalar(
        select(UserModel).where(
            UserModel.email == user_data.email, UserModel.username == user_data.username
        )
    )
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email или username уже существует"
        )

    new_user = UserModel(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hash_password(user_data.password)
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    verification_code = str(random.randint(10000000, 99999999))

    
    # Ключ 1: Hash с данными верификации
    await redis_client.hset(f"verification:{verification_code}", mapping={
        "code": verification_code,
        "user_id": str(new_user.id),
        "email": new_user.email
    })
    await redis_client.expire(f"verification:{verification_code}", 600)
    
    # Ключ 2: Быстрый поиск кода по email (чтобы не перебирать все ключи)
    await redis_client.set(f"verification:email:{new_user.email}", verification_code, ex=600)

    await send_verification_email(to=user_data.email, code=verification_code)

    return {"message": f"Код подтверждения отправлен на почту {user_data.email}"}




@router.post("/verify")
async def verify_code(
    verify_data: VerifyCode,
    db: AsyncSession = Depends(get_async_db),
    redis_client = Depends(get_redis)
):
    # Получаем данные из Redis Hash
    data = await redis_client.hgetall(f"verification:{verify_data.verify_code}")
    
    # Проверяем, существует ли код
    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ваш код неверный или истёк"
        )
    
    # Проверяем, совпадает ли код
    if data.get("code") != verify_data.verify_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ваш код неверный или истёк"
        )
    
    # Получаем user_id и конвертируем в int
    user_id = int(data.get("user_id"))
    
    # Находим пользователя в БД
    user = await db.scalar(
        select(UserModel).where(UserModel.id == user_id, UserModel.is_active == False)
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    user.is_active = True
    await db.commit()
    await db.refresh(user)

    # Удаляем ОБА ключа после успешной верификации
    await redis_client.delete(f"verification:{verify_data.verify_code}")
    # Удаляем ключ поиска по email (email берём из данных hash)
    email = data.get("email")
    if email:
        await redis_client.delete(f"verification:email:{email}")

    # Создаём токены
    token_data = {
        "sub": user.email,
        "role": user.role,
        "id": user.id
    }
    access_token = jwt_manager.create_access_token(token_data)
    refresh_token = jwt_manager.create_refresh_token(token_data)

    return {
        "message": f"Добро пожаловать, {user.username}!",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/resend-code")
async def resend_code(
    resend_data: ResendCodeSchema,
    db: AsyncSession = Depends(get_async_db),
    redis_client = Depends(get_redis)
):
    # 1. Находим старый код по email (быстрый поиск по новому ключу)
    old_code = await redis_client.get(f"verification:email:{resend_data.email}")
    
    # 2. Если код есть — удаляем оба старых ключа
    if old_code:
        await redis_client.delete(f"verification:{old_code}")
        await redis_client.delete(f"verification:email:{resend_data.email}")
    
    # 3. Проверяем, существует ли пользователь с таким email и не активирован
    user = await db.scalar(
        select(UserModel).where(UserModel.email == resend_data.email, UserModel.is_active == False)
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь с таким email не найден или уже активирован"
        )
    
    # 4. Генерируем новый код
    new_code = str(random.randint(10000000, 99999999))
    
    # 5. Сохраняем ОБА ключа 
    await redis_client.hset(f"verification:{new_code}", mapping={
        "code": new_code,
        "user_id": str(user.id),
        "email": user.email
    })
    await redis_client.expire(f"verification:{new_code}", 600)
    await redis_client.set(f"verification:email:{user.email}", new_code, ex=600)
    
    # 6. Отправляем email
    await send_verification_email(to=resend_data.email, code=new_code)
    
    return {"message": f"Код подтверждения отправлен на почту {resend_data.email}"}



@router.post("/token")
async def login(form_data : OAuth2PasswordRequestForm = Depends(), db : AsyncSession = Depends(get_async_db)):
    request_user = await db.scalars(
        select(UserModel)
        .where(UserModel.email == form_data.username, UserModel.is_active == True)
    )
    user = request_user.first()
    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неправильный пароль или емейл, или юзер не активен",
            headers={"WWW-Authenticate" : "Bearer"}
        )
    data = {
        "sub" : user.email,
        "role" : user.role,
        "id" : user.id
    }
    
    access_token = jwt_manager.create_access_token(data)
    refresh_token = jwt_manager.create_refresh_token(data)
    return {"access_token": access_token,"refresh_token" : refresh_token, "token_type": "bearer"}



@router.post("/access-token")
async def update_access_token(user : UserModel = Depends(jwt_validator.validate_refresh_token)):
    return await jwt_manager.new_access_token(user)


@router.post("/refresh-tokens")
async def update_refresh_token(user : UserModel = Depends(jwt_validator.validate_refresh_token)):
    return jwt_manager.new_refresh_token(user)


@router.post("/revoke-tokens")
async def logout(token_revoke : dict = Depends(jwt_manager.revoke_refresh_tokens)):
    return token_revoke

 
@router.delete("/{user_id}")
async def delete_account(
    user_id : int,
    db : AsyncSession = Depends(get_async_db),
    current_user : UserModel = Depends(jwt_validator.get_current_user)

) -> dict:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Только администратор может удалять пользователей")
    user = await db.scalar(select(UserModel).where(UserModel.id == user_id))
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Юзер не найден")
    await db.delete(user)
    await db.commit()
    return {"message" : "успешно!"}
    
    