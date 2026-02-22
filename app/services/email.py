import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from dotenv import load_dotenv
from os import getenv


load_dotenv()

async def send_verification_email(to: str, code: str):
    """
    Отправка email с кодом подтверждения
    
    Args:
        to: Email получателя
        code: Код подтверждения (например, "123456")
    """
    # 1. Создаём объект письма (контейнер для сообщения)
    # MIMEMultipart позволяет добавлять текст, HTML, вложения
    message = MIMEMultipart()
    
    # 2. Добавляем заголовок "От кого"
    message["From"] = getenv("SMTP_FROM") or getenv("SMTP_USER")
    
    # 3. Добавляем заголовок "Кому"
    # Email получателя, который передал пользователь
    message["To"] = to
    
    # 4. Добавляем заголовок "Тема письма"
    message["Subject"] = "Код подтверждения Cyberslate"
    
    
    body = f"""
    Привет!
    
    Твой код подтверждения для Cyberslate: {code}
    
    Введи этот код на сайте для завершения регистрации.
    
    Код действителен 10 минут.
    
    Если ты не регистрировался - просто проигнорируй это письмо.
    """
    
    # 6. Добавляем текст письма в контейнер
    # MIMEText создаёт текстовую часть
    # "plain" = простой текст (не HTML)
    # "utf-8" = кодировка (поддерживает кириллицу)
    message.attach(MIMEText(body, "plain", "utf-8"))
    
    # 7. Отправляем письмо через SMTP сервер
    # aiosmtplib.send - асинхронная отправка
     
    await aiosmtplib.send(
        message,
        sender=getenv("SMTP_FROM"),
        hostname=getenv("SMTP_HOST"),
        port=getenv("SMTP_PORT"),
        username=getenv("SMTP_USER"),
        password=getenv("SMTP_PASSWORD"),
        start_tls=False,
    )
