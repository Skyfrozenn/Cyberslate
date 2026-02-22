from pydantic import BaseModel, Field, field_validator, EmailStr, ConfigDict, PositiveInt
from datetime import datetime
from typing import Optional


class UserCreateSchema(BaseModel):
    username : str = Field(..., min_length=3, max_length=20, description="Никнейм от 3-29 символов")
    email : EmailStr = Field(..., description="Email пользователя")
    password : str = Field(..., min_length=8, description="Пароль от 8 символов")

    @field_validator("password")
    @classmethod
    def validation_password(cls, value):

        if not any(item.isupper() for item in value):
            raise ValueError("В пароле должен быть хоть один большой символ!")
        special_characters = "!@#$%^&*()_+/,.?[]"
        if not any(item  in special_characters for item in value):
            raise ValueError(f" В пароде должен быть хоть один спецсимвол {special_characters}")
        return value


class UserResponseSchema(BaseModel):
    id: PositiveInt
    username: str
    email: EmailStr
    created_at: datetime
    updated_at: datetime
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class VerifyCode(BaseModel):
    verify_code : str = Field(..., description="Код подтверждения из 8 цифр")

    @field_validator("verify_code")
    @classmethod
    def validate_verify_code(cls, value):
        if not value.isdigit():
            raise ValueError("Код должен содержать только цифры!")
        if len(value) != 8:
            raise ValueError("Код должен содержать ровно 8 цифр!")
        return value



class RefreshToken(BaseModel):
    refresh_token: str


class RefreshTokenlist(BaseModel):
    refresh_tokens : list[RefreshToken] = Field(..., description="Список рефреш токенов")


class ResendCodeSchema(BaseModel):
    email: EmailStr = Field(..., description="Email для повторной отправки кода")



    

