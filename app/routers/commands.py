from fastapi import APIRouter, Depends, HTTPException, status, Query

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload


from app.schemas.users import UserResponseSchema
from app.schemas.commands import CommandCreateSchema, CommandResponseSchema, CommandSearchSchema
from app.models import CommandModel, UserModel

from app.db_depends import get_async_db
from app.validation.hash_password import hash_password
from app.utilits import get_command, team_rights, check_has_team


router = APIRouter(
    prefix="/commands",
    tags = ["Commands"]
)


@router.post("/", response_model=CommandResponseSchema, status_code=status.HTTP_201_CREATED)
async def new_command(
    create_command : CommandCreateSchema,
    db : AsyncSession = Depends(get_async_db),
    user : UserModel =  Depends(check_has_team) #проверка состоит ли юзер уже в команде
) -> CommandResponseSchema:
    
    command = await db.scalar(select(CommandModel).where(CommandModel.name == create_command.name))
    if command is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Команда с таким именем уже существует!")
    
    hashed_password = hash_password(create_command.password)
    new_command = CommandModel(
        name = create_command.name,
        password = hashed_password
    )

    new_command.users.append(user)
    user.is_team_creator = True

    db.add(new_command)
    await db.commit()
    await db.refresh(new_command)
    result = await get_command(new_command.id, db)
    return result

    

@router.get("/{command_id}", response_model=CommandResponseSchema)
async def get_info_command(
    command_id : int,
    db : AsyncSession = Depends(get_async_db)
) -> CommandResponseSchema:
    command = await get_command(command_id, db)
    return command
    
    
@router.delete("/{сommand_id}")
async def delete_command(
    command_id : int,
    db : AsyncSession = Depends(get_async_db),
    rights_check = Depends(team_rights)    
):
    
    command = await db.scalar(select(CommandModel).where(CommandModel.id == command_id))
    await db.delete(command)
    await db.commit()
    return {"message" : "Команда удалена!"}




@router.get("/", response_model=CommandSearchSchema)
async def search_commands(
    search_name: str | None = Query(None, description="Поиск по названию команды"),
    status: str | None = Query(None, pattern=r"^(active|inactive)$", description="Статус [active|inactive]"),
    is_filled: bool | None = Query(None, description="Заполненность команды"),
    last_id: int | None = Query(None, ge=1, description="ID для курсорной пагинации"),
    db: AsyncSession = Depends(get_async_db),
) -> CommandSearchSchema:
    
    PAGE_SIZE = 20

    # Базовые фильтры
    filters  = []   

    if status: #активная или нет
        filters.append(CommandModel.status == status)
    
    if is_filled: #полная команда или нет
        filters.append(CommandModel.is_filled == is_filled)

   

    rank = None

    # Полнотекстовый поиск
    if search_name:
        search_value = search_name.strip()
        if search_value:
            # TSQuery для двух языков
            ts_query_ru = func.websearch_to_tsquery("russian", search_value)
            ts_query_en = func.websearch_to_tsquery("english", search_value)

            # Поиск по TSVECTOR
            fst_search = or_(
                CommandModel.tsv.op("@@")(ts_query_ru),
                CommandModel.tsv.op("@@")(ts_query_en),
            )

            # Trigram для опечаток 
            trigram_search = or_(
                CommandModel.name.op("%")(search_value),
                func.similarity(CommandModel.name, search_value) > 0.15,
            )

            filters.append(or_(fst_search, trigram_search))

            # Ранжирование
            rank = func.greatest(
                func.ts_rank_cd(CommandModel.tsv, ts_query_ru),
                func.ts_rank_cd(CommandModel.tsv, ts_query_en),
                func.similarity(CommandModel.name, search_value) * 0.5,
            )


    if rank is None and last_id: #проверка что нет поиска и есть ласт айди курсор пагинация
        filters.append(CommandModel.id > last_id)

    # Запрос
    stmt = (
        select(CommandModel)
        .where(*filters)
        .options(selectinload(CommandModel.users))  # подгружаем участников
        .limit(PAGE_SIZE)
    )

    # Сортировка
    if rank is not None:
        stmt = stmt.order_by(rank.desc())
    else:
        stmt = stmt.order_by(CommandModel.created_at.desc())

    result = await db.execute(stmt)
    commands = result.scalars().all()

    # Конвертация в схемы
    items = [
        CommandResponseSchema(
            id=cmd.id,
            name=cmd.name,
            created_at=cmd.created_at,
            updated_at=cmd.updated_at,
            status=cmd.status,
            is_filled=cmd.is_filled,
            users=[
                UserResponseSchema(
                    id=u.id,
                    username=u.username,
                    email=u.email,
                    created_at=u.created_at,
                    updated_at=u.updated_at,
                    command_id = u.command_id,
                    role=u.role,
                    is_active=u.is_active,
                    is_team_creator=u.is_team_creator,
                )
                for u in cmd.users
            ]
        )
        for cmd in commands
    ]

    last_id_in_results = items[-1].id if items else None

    return CommandSearchSchema(
        next_cursor = last_id_in_results,
        items = items,
    )