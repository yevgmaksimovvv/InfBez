"""
Модуль для работы с паролями: хеширование и верификация
"""
import secrets
from algorithms.streebog.streebog import streebog_512


def hash_password(password: str) -> str:
    """
    Хеширует пароль с солью используя Streebog-512

    Args:
        password: Пароль для хеширования

    Returns:
        str: salt:hash в шестнадцатеричном формате
    """
    salt = secrets.token_bytes(32)
    salted_password = salt + password.encode('utf-8')
    password_hash = streebog_512(salted_password)
    return f"{salt.hex()}:{password_hash.hex()}"


def verify_password(stored_hash: str, password: str) -> bool:
    """
    Проверяет хеш пароля с защитой от timing-атак

    Args:
        stored_hash: Сохраненный хеш в формате "salt:hash"
        password: Пароль для проверки

    Returns:
        bool: True если пароль совпадает
    """
    try:
        salt_hex, hash_hex = stored_hash.split(':')
        salt = bytes.fromhex(salt_hex)
        salted_password = salt + password.encode('utf-8')
        computed_hash = streebog_512(salted_password).hex()
        return secrets.compare_digest(computed_hash, hash_hex)
    except (ValueError, AttributeError):
        return False
