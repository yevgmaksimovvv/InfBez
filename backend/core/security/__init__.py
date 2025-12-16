"""
Модуль безопасности с разделением ответственности
"""
from backend.core.security.password_security import hash_password, verify_password
from backend.core.security.jwt_security import create_access_token, decode_token
from backend.core.security.otp_security import (
    generate_otp,
    hash_otp,
    verify_otp,
    create_otp_hash
)

__all__ = [
    # Password
    "hash_password",
    "verify_password",
    # JWT
    "create_access_token",
    "decode_token",
    # OTP
    "generate_otp",
    "hash_otp",
    "verify_otp",
    "create_otp_hash",
]
