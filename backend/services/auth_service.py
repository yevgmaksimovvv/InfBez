"""
Сервис для бизнес-логики аутентификации
"""
import logging
from sqlalchemy.orm import Session
from fastapi import HTTPException

from backend.models import User, UserRole
from backend.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    verify_otp
)

logger = logging.getLogger(__name__)


class AuthService:
    """Сервис для аутентификации пользователей"""

    @staticmethod
    def register_user(username: str, email: str, password: str, db: Session) -> User:
        """
        Регистрация нового пользователя

        Args:
            username: Имя пользователя
            email: Email
            password: Пароль
            db: Database session

        Returns:
            User: Созданный пользователь

        Raises:
            ValueError: Если пользователь уже существует
        """
        # Проверка существования пользователя с указанным именем или email
        if db.query(User).filter(User.username == username).first():
            logger.warning(f"Registration attempt with existing username: {username}")
            raise ValueError("Username already exists")

        if db.query(User).filter(User.email == email).first():
            logger.warning(f"Registration attempt with existing email: {email}")
            raise ValueError("Email already exists")

        # Хеширование пароля с использованием алгоритма Стрибог-512 и соли
        password_hash = hash_password(password)

        # Создание записи пользователя в базе данных
        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            role=UserRole.USER
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        logger.info(f"New user registered: {user.username} (ID: {user.id})")

        return user

    @staticmethod
    def authenticate_user(
        username: str,
        password: str,
        otp_code: str,
        db: Session
    ) -> tuple[User, str]:
        """
        Аутентификация пользователя с проверкой пароля и OTP

        Args:
            username: Имя пользователя
            password: Пароль
            otp_code: OTP код (опционально)
            db: Database session

        Returns:
            tuple: (User, access_token)

        Raises:
            ValueError: Если аутентификация неудачна
        """
        user = db.query(User).filter(User.username == username).first()

        if not user:
            logger.warning(f"Login attempt with non-existent username: {username}")
            raise ValueError("Invalid credentials")

        # Первый фактор аутентификации: проверка пароля
        if not verify_password(user.password_hash, password):
            logger.warning(f"Failed login attempt for user: {username} (invalid password)")
            raise ValueError("Invalid credentials")

        # Третий фактор аутентификации: одноразовый пароль (если предоставлен)
        if otp_code:
            if not verify_otp(user.otp_secret, otp_code):
                logger.warning(f"Failed OTP verification for user: {username}")
                raise ValueError("Invalid OTP")

        # Создание токена доступа
        access_token = create_access_token(
            data={"sub": user.username, "role": user.role.value}
        )

        logger.info(f"Successful login for user: {user.username}")

        return user, access_token

    @staticmethod
    def update_user_otp(user: User, otp_hash: str, db: Session) -> None:
        """
        Обновление секретного ключа одноразового пароля пользователя

        Args:
            user: Пользователь
            otp_hash: Хеш одноразового пароля для сохранения
            db: Database session
        """
        user.otp_secret = otp_hash
        db.commit()
        logger.info(f"OTP updated for user: {user.username}")
