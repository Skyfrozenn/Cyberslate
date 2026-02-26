from pydantic import BaseModel, Field, field_validator, ConfigDict, PositiveInt
from datetime import datetime

from app.schemas.users import UserResponseSchema

class CommandCreateSchema(BaseModel):
    name: str = Field(..., min_length=3, max_length=50, description="Название команды от 3 до 50 символов")
    password: str = Field(..., min_length=8, description="Пароль от 8 символов")

    @field_validator("password")
    @classmethod
    def validation_password(cls, value):
        if not any(item.isupper() for item in value):
            raise ValueError("В пароле должен быть хоть один большой символ!")
        special_characters = "!@#$%^&*()_+/,.?[]"
        if not any(item in special_characters for item in value):
            raise ValueError(f" В пароде должен быть хоть один спецсимвол {special_characters}")
        return value


class CommandResponseSchema(BaseModel):
    id: PositiveInt
    name: str
    created_at: datetime
    updated_at: datetime
    status: str
    is_filled: bool

    users : list[UserResponseSchema] #для селетионлоад

    model_config = ConfigDict(from_attributes=True)



class JoinCommandResponce(BaseModel):
    password : str = Field(..., min_length=8, description="Пароль от 8 символов")

    @field_validator("password")
    @classmethod
    def validation_password(cls, value):
        if not any(item.isupper() for item in value):
            raise ValueError("В пароле должен быть хоть один большой символ!")
        special_characters = "!@#$%^&*()_+/,.?[]"
        if not any(item in special_characters for item in value):
            raise ValueError(f" В пароде должен быть хоть один спецсимвол {special_characters}")
        return value



class CommandSearchSchema(BaseModel):
    next_cursor: int | None
    items: list[CommandResponseSchema]