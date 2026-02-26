from fastapi import Depends, HTTPException, status

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
 
from app.validation.jwt_validation import jwt_validator
from app.schemas.commands import CommandResponseSchema

from app.models import UserModel, CommandModel
from app.db_depends import get_async_db

 



async def check_has_role(current_user : UserModel = Depends(jwt_validator.get_current_user)):
    """
    Проверяет есть ли у юзера роль
    """
    if current_user.role != "player" and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Смените роль на player,чтобы присоединиться к команде или создать ее")
    return current_user


async def check_no_role(current_user : UserModel = Depends(jwt_validator.get_current_user)):
        """
        Проверяет что юзер уже имеет роль
        """
        if current_user.role == "player" or current_user.role == "admin":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Вы уже можете учавствовать в матчах и создавать команды!")
        return current_user
        


async def get_command(command_id : int, db : AsyncSession) -> CommandResponseSchema:
    command = await db.scalar(
          select(CommandModel)
          .where(CommandModel.id == command_id, CommandModel.status == "active")
          .options(selectinload(CommandModel.users))
     )

    return CommandResponseSchema(
         id = command.id,
         name = command.name,
         created_at = command.created_at,
         updated_at = command.updated_at,
         status = command.status,
         is_filled = command.is_filled,
         users = command.users
    )
    

async def team_rights(command_id : int, user : UserModel = Depends(check_has_role)):
     """
     Проверяет что у юзера есть роль
     и это его команда
     """
     if user.role != "admin":
        if user.is_team_creator == "False" or user.command_id != command_id:
          raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="К команде нет доступа!")
        return user
     
     
async def check_has_team(user : UserModel = Depends(check_has_role)):
    """
    Проверка есть ли юзер уже в команде
    """
    if user.command_id is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Вы уже состоите в команде!")
    return user