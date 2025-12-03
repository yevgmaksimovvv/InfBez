"""
Утилиты для аутентификации
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from fastapi import HTTPException
from backend.models import User
import os
import random
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password_hash(stored_hash: str, password_hash: str) -> bool:
    """Проверка хеша пароля (Стрибог)"""
    return stored_hash == password_hash


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Создание JWT токена"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user(token: str, db: Session) -> User:
    """Получение текущего пользователя из токена"""
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user


def verify_otp(user: User, otp_code: str) -> bool:
    """Проверка OTP кода"""
    # Упрощенная версия - в реальности нужно проверять время и хешировать
    return user.otp_secret == otp_code


def send_otp_email(email: str) -> str:
    """Отправка OTP на email"""
    # Генерируем 6-значный код
    otp_code = str(random.randint(100000, 999999))
    
    # Отправляем email (упрощенная версия)
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    
    if all([smtp_host, smtp_user, smtp_password]):
        try:
            msg = MIMEText(f"Your OTP code is: {otp_code}")
            msg['Subject'] = "CyberSecurity OTP Code"
            msg['From'] = smtp_user
            msg['To'] = email
            
            server = smtplib.SMTP(smtp_host, smtp_port)
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
            server.quit()
        except Exception as e:
            print(f"Error sending email: {e}")
    
    return otp_code

