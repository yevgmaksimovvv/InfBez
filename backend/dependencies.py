"""
Общие зависимости для API эндпоинтов
"""
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.core.security import decode_token
from backend.models import User

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Получает текущего аутентифицированного пользователя из JWT токена

    Args:
        credentials: Bearer токен из запроса
        db: Сессия базы данных

    Returns:
        User: Текущий аутентифицированный пользователь

    Raises:
        HTTPException: Если токен невалиден или пользователь не найден
    """
    payload = decode_token(credentials.credentials)
    username: str = payload.get("sub")

    if username is None:
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user
