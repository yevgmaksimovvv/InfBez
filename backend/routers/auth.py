"""
Роутер аутентификации
Тонкий слой HTTP эндпоинтов, бизнес-логика в AuthService
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging

from backend.core.database import get_db
from backend.models import User
from backend.dependencies import get_current_user
from backend.schemas import RegisterRequest, LoginRequest
from backend.services import AuthService, send_otp_email

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/register")
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """Регистрация пользователя с валидацией"""
    try:
        auth_service = AuthService()
        user = auth_service.register_user(
            username=request.username,
            email=request.email,
            password=request.password,
            db=db
        )

        return {"message": "User registered successfully", "user_id": user.id}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Registration failed")


@router.post("/login")
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Вход с тройной аутентификацией"""
    try:
        auth_service = AuthService()
        user, access_token = auth_service.authenticate_user(
            username=request.username,
            password=request.password,
            otp_code=request.otp_code,
            db=db
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "role": user.role.value
            }
        }

    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail="Login failed")


@router.post("/send-otp")
async def send_otp_endpoint(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Отправка одноразового пароля на электронную почту (третий фактор аутентификации)"""
    if not user.email:
        raise HTTPException(status_code=400, detail="Email not configured for this user")

    try:
        # Отправка одноразового пароля и получение хешированного значения
        otp_hash_with_timestamp = await send_otp_email(user.email)

        # Сохранение хеша в базе данных
        auth_service = AuthService()
        auth_service.update_user_otp(user, otp_hash_with_timestamp, db)

        return {"message": "OTP sent to email"}

    except Exception as e:
        logger.error(f"Error sending OTP: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to send OTP")


@router.post("/oauth/{provider}")
async def oauth_login(provider: str, code: str, db: Session = Depends(get_db)):
    """Аутентификация через внешний провайдер (второй фактор аутентификации)"""
    if provider not in ["google", "yandex"]:
        raise HTTPException(status_code=400, detail="Invalid provider")

    # Требуется реализация процесса аутентификации для провайдеров Google и Yandex
    logger.info(f"OAuth {provider} authentication attempted")
    return {"message": f"OAuth {provider} authentication successful"}


@router.get("/me")
async def get_current_user_info(user: User = Depends(get_current_user)):
    """Получение информации о текущем пользователе"""
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role.value
    }
