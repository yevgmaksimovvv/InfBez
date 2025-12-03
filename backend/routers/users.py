"""
Users router
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.auth_utils import get_current_user
from backend.models import User, UserRole

router = APIRouter()
security = HTTPBearer()


@router.get("/")
async def get_users(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Получить список пользователей (только для админов)"""
    current_user = get_current_user(credentials.credentials, db)
    
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    users = db.query(User).all()
    return [{"id": u.id, "username": u.username, "role": u.role.value} for u in users]

