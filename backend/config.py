"""
Конфигурация приложения
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Настройки приложения"""

    # Настройки токенов доступа
    SECRET_KEY: str = os.getenv("SECRET_KEY", "CHANGE_ME_IN_PRODUCTION")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

    # Настройки одноразовых паролей
    OTP_EXPIRE_MINUTES: int = int(os.getenv("OTP_EXPIRE_MINUTES", "5"))

    # Настройки базы данных
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/cybersecurity"
    )

    # Настройки кэша Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    REDIS_ENABLED: bool = os.getenv("REDIS_ENABLED", "false").lower() == "true"

    # Настройки почтового сервера
    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")

    # Главный ключ для шифрования приватных ключей
    MASTER_KEY: str = os.getenv("MASTER_KEY", "")

    # Настройки ограничения частоты запросов
    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    RATE_LIMIT_PER_HOUR: int = int(os.getenv("RATE_LIMIT_PER_HOUR", "1000"))

    # Настройки разрешенных источников запросов
    CORS_ORIGINS: list = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://localhost:5173"
    ).split(",")

    # Ограничения для криптографических операций
    MAX_TEXT_LENGTH: int = int(os.getenv("MAX_TEXT_LENGTH", "100000"))  # 100 КБ
    MAX_KUZNECHIK_BLOCK: int = int(os.getenv("MAX_KUZNECHIK_BLOCK", "1000000"))  # 1 МБ
    MAX_RSA_BLOCK: int = int(os.getenv("MAX_RSA_BLOCK", "4090"))  # ~4 КБ
    MAX_RSA_KEYS_PER_USER: int = int(os.getenv("MAX_RSA_KEYS_PER_USER", "10"))


settings = Settings()
