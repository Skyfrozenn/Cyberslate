from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated = "auto")

def hash_password(password : str) -> str:
    """
    Генерирует пароль в ХЕШ
    с использованием bcrypt
    """
    return pwd_context.hash(password)



def verify_password(plain_password : str, hash_password : str) -> bool:
    """
    Проверяет соответсвует ли введеный пароль хешу в бд
    """
    return pwd_context.verify(plain_password, hash_password)