"""
Crypto operations router
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel
from backend.database import get_db
from backend.auth_utils import get_current_user
from backend.models import User
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from algorithms.kuznechik.kuznechik import Kuznechik
from algorithms.rsa_32768 import RSA32768
from algorithms.streebog.streebog import streebog_512

router = APIRouter()
security = HTTPBearer()


class EncryptRequest(BaseModel):
    text: str
    algorithm: str  # "rsa" или "kuznechik"


class DecryptRequest(BaseModel):
    encrypted_data: str
    algorithm: str
    key: str = None  # Для Кузнечика


@router.post("/encrypt")
async def encrypt_text(
    request: EncryptRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Шифрование текста"""
    user = get_current_user(credentials.credentials, db)
    
    if request.algorithm == "kuznechik":
        # Генерируем ключ или используем существующий
        kuz = Kuznechik()
        key = kuz.keys[0].hex()
        
        # Шифруем по блокам 16 байт
        text_bytes = request.text.encode('utf-8')
        encrypted_blocks = []
        
        # Дополняем до кратности 16 байт
        padding = 16 - (len(text_bytes) % 16)
        if padding != 16:
            text_bytes += bytes([padding] * padding)
        
        for i in range(0, len(text_bytes), 16):
            block = text_bytes[i:i+16]
            encrypted_block = kuz.encrypt(block)
            encrypted_blocks.append(encrypted_block.hex())
        
        return {
            "encrypted": "".join(encrypted_blocks),
            "key": key,
            "algorithm": "kuznechik"
        }
    
    elif request.algorithm == "rsa":
        rsa = RSA32768()
        encrypted = rsa.encrypt(request.text.encode('utf-8'))
        
        return {
            "encrypted": encrypted.hex(),
            "algorithm": "rsa",
            "public_key": str(rsa.public_key),
            "private_key": str(rsa.private_key)  # В реальности не отправлять!
        }
    
    else:
        raise HTTPException(status_code=400, detail="Invalid algorithm")


@router.post("/decrypt")
async def decrypt_text(
    request: DecryptRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Расшифрование текста"""
    user = get_current_user(credentials.credentials, db)
    
    if request.algorithm == "kuznechik":
        if not request.key:
            raise HTTPException(status_code=400, detail="Key required for Kuznechik")
        
        kuz = Kuznechik(key=bytes.fromhex(request.key))
        encrypted_bytes = bytes.fromhex(request.encrypted_data)
        
        decrypted_blocks = []
        for i in range(0, len(encrypted_bytes), 16):
            block = encrypted_bytes[i:i+16]
            decrypted_block = kuz.decrypt(block)
            decrypted_blocks.append(decrypted_block)
        
        decrypted = b"".join(decrypted_blocks)
        # Убираем padding
        padding = decrypted[-1]
        decrypted = decrypted[:-padding]
        
        return {"decrypted": decrypted.decode('utf-8')}
    
    elif request.algorithm == "rsa":
        # В реальности нужно сохранять ключи в БД
        raise HTTPException(status_code=501, detail="RSA decryption not fully implemented")
    
    else:
        raise HTTPException(status_code=400, detail="Invalid algorithm")


@router.post("/hash")
async def hash_text(
    text: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Хеширование текста Стрибогом-512"""
    user = get_current_user(credentials.credentials, db)
    
    hash_result = streebog_512(text.encode('utf-8'))
    
    return {"hash": hash_result.hex()}

