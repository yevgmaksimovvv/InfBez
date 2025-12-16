"""
FastAPI Backend для веб-приложения информационной безопасности
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import logging
from logging.handlers import RotatingFileHandler

from backend.routers import auth, crypto, users, documents
from backend.core import Base, engine
from backend.config import settings
from backend.middleware import RateLimitMiddleware

# Настройка логирования
os.makedirs('logs', exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler(
            'logs/app.log',
            maxBytes=10485760,  # 10MB
            backupCount=5
        ),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Менеджер контекста жизненного цикла для событий запуска/остановки"""
    # Запуск
    logger.info("Starting CyberSecurity API...")

    # Создание таблиц базы данных
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")

    if settings.REDIS_ENABLED:
        logger.info("Redis rate limiting enabled")
    else:
        logger.info("In-memory rate limiting enabled")

    logger.info(
        f"Rate limiting: {settings.RATE_LIMIT_PER_MINUTE} req/min, "
        f"{settings.RATE_LIMIT_PER_HOUR} req/hour"
    )

    yield

    # Остановка
    logger.info("Shutting down CyberSecurity API...")


app = FastAPI(
    title="CyberSecurity API",
    version="2.0.0",
    description="Secure cryptographic operations API with GOST algorithms",
    lifespan=lifespan
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
    expose_headers=["Content-Disposition"],
)

# Ограничение запросов
app.add_middleware(RateLimitMiddleware)

# Подключение роутеров
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(crypto.router, prefix="/api/crypto", tags=["crypto"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])


@app.get("/")
async def root():
    """Корневой эндпоинт API"""
    return {
        "message": "CyberSecurity API",
        "version": "2.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    """Эндпоинт проверки здоровья"""
    return {
        "status": "ok",
        "redis_enabled": settings.REDIS_ENABLED,
        "rate_limit_enabled": settings.RATE_LIMIT_ENABLED
    }
