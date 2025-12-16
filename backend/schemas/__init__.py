"""
Pydantic схемы для валидации данных
"""
from backend.schemas.auth_schemas import RegisterRequest, LoginRequest, OAuthCallback
from backend.schemas.crypto_schemas import EncryptRequest, DecryptRequest, HashRequest
from backend.schemas.document_schemas import CreateDocumentRequest

__all__ = [
    # Auth
    "RegisterRequest",
    "LoginRequest",
    "OAuthCallback",
    # Crypto
    "EncryptRequest",
    "DecryptRequest",
    "HashRequest",
    # Documents
    "CreateDocumentRequest",
]
