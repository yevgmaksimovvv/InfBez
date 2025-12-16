"""
Pydantic схемы для криптографических операций
"""
from pydantic import BaseModel, field_validator
import uuid
from backend.config import settings


class EncryptRequest(BaseModel):
    text: str
    algorithm: str

    @field_validator('text')
    @classmethod
    def validate_text(cls, v):
        if len(v) == 0:
            raise ValueError("Text cannot be empty")
        if len(v.encode('utf-8')) > settings.MAX_TEXT_LENGTH:
            raise ValueError(f"Text too long (max {settings.MAX_TEXT_LENGTH} bytes)")
        return v

    @field_validator('algorithm')
    @classmethod
    def validate_algorithm(cls, v):
        if v not in ["rsa", "kuznechik"]:
            raise ValueError("Algorithm must be 'rsa' or 'kuznechik'")
        return v


class DecryptRequest(BaseModel):
    encrypted_data: str
    algorithm: str
    key: str = None
    key_id: str = None

    @field_validator('algorithm')
    @classmethod
    def validate_algorithm(cls, v):
        if v not in ["rsa", "kuznechik"]:
            raise ValueError("Algorithm must be 'rsa' or 'kuznechik'")
        return v

    @field_validator('key_id')
    @classmethod
    def validate_key_id(cls, v):
        if v is not None:
            try:
                uuid.UUID(v)
            except ValueError:
                raise ValueError("key_id must be a valid UUID")
        return v


class HashRequest(BaseModel):
    text: str

    @field_validator('text')
    @classmethod
    def validate_text(cls, v):
        if len(v.encode('utf-8')) > settings.MAX_TEXT_LENGTH:
            raise ValueError(f"Text too long (max {settings.MAX_TEXT_LENGTH} bytes)")
        return v
