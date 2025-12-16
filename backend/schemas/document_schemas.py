"""
Pydantic схемы для документов
"""
from pydantic import BaseModel


class CreateDocumentRequest(BaseModel):
    original_text: str
    encrypted_text: str = None
    algorithm: str = None
