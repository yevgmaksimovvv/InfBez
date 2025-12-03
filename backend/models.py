"""
Database models
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Enum as SQLEnum
from sqlalchemy.sql import func
from backend.database import Base
import enum


class UserRole(str, enum.Enum):
    GUEST = "guest"
    USER = "user"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)
    password_hash = Column(String, nullable=False)  # Хеш Стрибог-512
    role = Column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)
    
    # Тройная аутентификация
    google_id = Column(String, unique=True, nullable=True)
    yandex_id = Column(String, unique=True, nullable=True)
    email_verified = Column(Boolean, default=False)
    otp_secret = Column(String, nullable=True)  # Для одноразовых паролей
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    original_text = Column(Text, nullable=False)
    encrypted_text = Column(Text, nullable=True)
    algorithm = Column(String, nullable=False)  # "rsa" или "kuznechik"
    encryption_key = Column(Text, nullable=True)  # Зашифрованный ключ
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

