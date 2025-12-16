"""
Модуль для работы с OTP (One-Time Password)
"""
import secrets
from datetime import datetime
from algorithms.streebog.streebog import streebog_512
from backend.config import settings


def hash_otp(otp_code: str, timestamp: str) -> str:
    """
    Хеширование одноразового пароля с временной меткой

    Args:
        otp_code: Одноразовый пароль
        timestamp: Временная метка в формате ISO

    Returns:
        str: Хеш в шестнадцатеричном формате
    """
    combined = f"{otp_code}:{timestamp}"
    return streebog_512(combined.encode()).hex()


def generate_otp() -> tuple[str, str]:
    """
    Генерация одноразового пароля и временной метки

    Returns:
        tuple: Кортеж (код одноразового пароля, временная метка в формате ISO)
    """
    otp_code = str(secrets.randbelow(900000) + 100000)
    timestamp = datetime.utcnow().isoformat()
    return otp_code, timestamp


def verify_otp(stored_otp_data: str, otp_code: str) -> bool:
    """
    Проверка одноразового пароля с защитой от временных атак

    Args:
        stored_otp_data: Сохраненные данные в формате "hash:timestamp"
        otp_code: Одноразовый пароль для проверки

    Returns:
        bool: True, если одноразовый пароль действителен
    """
    if not stored_otp_data:
        return False

    try:
        stored_hash, timestamp_str = stored_otp_data.split(":")
        timestamp = datetime.fromisoformat(timestamp_str)

        # Проверка срока действия одноразового пароля
        now = datetime.utcnow()
        if (now - timestamp).total_seconds() > settings.OTP_EXPIRE_MINUTES * 60:
            return False

        # Проверка хеша с защитой от временных атак
        otp_hash = hash_otp(otp_code, timestamp_str)
        return secrets.compare_digest(otp_hash, stored_hash)
    except (ValueError, AttributeError):
        return False


def create_otp_hash(otp_code: str, timestamp: str) -> str:
    """
    Создание хеша одноразового пароля для хранения

    Args:
        otp_code: Одноразовый пароль
        timestamp: Временная метка в формате ISO

    Returns:
        str: Строка в формате "hash:timestamp" для хранения
    """
    otp_hash = hash_otp(otp_code, timestamp)
    return f"{otp_hash}:{timestamp}"
