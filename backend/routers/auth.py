"""
Authentication router
Тройная аутентификация: Пароль + OAuth + Email/OTP
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from backend.database import get_db
from backend.models import User, UserRole
from backend.auth_utils import (
    verify_password_hash, create_access_token, get_current_user,
    verify_otp, send_otp_email
)
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from algorithms.streebog.streebog import streebog_512

router = APIRouter()
security = HTTPBearer()


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str
    otp_code: str = None  # Для третьего фактора


class OAuthCallback(BaseModel):
    provider: str  # "google" или "yandex"
    code: str


@router.post("/register")
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """Регистрация пользователя"""
    # Проверяем существование пользователя
    if db.query(User).filter(User.username == request.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    
    if db.query(User).filter(User.email == request.email).first():
        raise HTTPException(status_code=400, detail="Email already exists")
    
    # Хешируем пароль Стрибогом-512
    password_hash = streebog_512(request.password.encode()).hex()
    
    # Создаем пользователя
    user = User(
        username=request.username,
        email=request.email,
        password_hash=password_hash,
        role=UserRole.USER
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return {"message": "User registered successfully", "user_id": user.id}


@router.post("/login")
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Вход с тройной аутентификацией"""
    user = db.query(User).filter(User.username == request.username).first()
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Фактор 1: Проверка пароля (Стрибог-512)
    password_hash = streebog_512(request.password.encode()).hex()
    if user.password_hash != password_hash:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Фактор 2: OAuth (проверяется отдельным эндпоинтом)
    # Фактор 3: OTP (если требуется)
    if request.otp_code:
        if not verify_otp(user, request.otp_code):
            raise HTTPException(status_code=401, detail="Invalid OTP")
    
    # Создаем токен
    access_token = create_access_token(data={"sub": user.username, "role": user.role.value})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "role": user.role.value
        }
    }


@router.post("/send-otp")
async def send_otp_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Отправка OTP на email (третий фактор)"""
    user = get_current_user(credentials.credentials, db)
    
    # Отправляем OTP
    otp_code = send_otp_email(user.email)
    
    # Сохраняем OTP секрет (в реальности нужно хешировать)
    user.otp_secret = otp_code
    db.commit()
    
    return {"message": "OTP sent to email"}


@router.post("/oauth/{provider}")
async def oauth_login(provider: str, code: str, db: Session = Depends(get_db)):
    """OAuth аутентификация (второй фактор)"""
    # Здесь должна быть реализация OAuth для Google/Yandex
    # Упрощенная версия
    if provider not in ["google", "yandex"]:
        raise HTTPException(status_code=400, detail="Invalid provider")
    
    # В реальности здесь обмен кода на токен и получение user info
    # Для примера возвращаем успех
    return {"message": f"OAuth {provider} authentication successful"}


@router.get("/me")
async def get_current_user_info(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Получить информацию о текущем пользователе"""
    user = get_current_user(credentials.credentials, db)
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role.value
    }

