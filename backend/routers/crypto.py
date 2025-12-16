"""
Роутер криптографических операций
Тонкий слой HTTP эндпоинтов, вся логика в сервисах
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging

from backend.core.database import get_db
from backend.models import User
from backend.dependencies import get_current_user
from backend.schemas import EncryptRequest, DecryptRequest, HashRequest
from backend.services import KuznechikService, RSAService, HashService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/encrypt")
async def encrypt_text(
    request: EncryptRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Шифрование текста с безопасным управлением ключами"""
    try:
        if request.algorithm == "kuznechik":
            kuznechik_service = KuznechikService()
            encrypted_hex, key = kuznechik_service.encrypt(request.text)

            logger.info(f"User {user.username} encrypted text with Kuznechik")

            return {
                "encrypted": encrypted_hex,
                "key": key,
                "algorithm": "kuznechik"
            }

        elif request.algorithm == "rsa":
            rsa_service = RSAService()
            result = rsa_service.encrypt(request.text, user, db)

            return {
                "encrypted": result["encrypted"],
                "algorithm": "rsa",
                "key_id": result["key_id"],
                "public_key": result["public_key"]
            }

        else:
            raise HTTPException(status_code=400, detail="Invalid algorithm")

    except ValueError as e:
        logger.error(f"Validation error during encryption: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error during encryption: {str(e)}")
        raise HTTPException(status_code=500, detail="Encryption failed")


@router.post("/decrypt")
async def decrypt_text(
    request: DecryptRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Расшифрование текста с использованием сохраненных ключей"""
    try:
        if request.algorithm == "kuznechik":
            if not request.key:
                raise HTTPException(status_code=400, detail="Key required for Kuznechik")

            kuznechik_service = KuznechikService()
            decrypted = kuznechik_service.decrypt(request.encrypted_data, request.key)

            logger.info(f"User {user.username} decrypted text with Kuznechik")

            return {"decrypted": decrypted}

        elif request.algorithm == "rsa":
            if not request.key_id:
                raise HTTPException(status_code=400, detail="key_id required for RSA decryption")

            rsa_service = RSAService()
            decrypted = rsa_service.decrypt(request.encrypted_data, request.key_id, user, db)

            return {"decrypted": decrypted}

        else:
            raise HTTPException(status_code=400, detail="Invalid algorithm")

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error during decryption: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error during decryption: {str(e)}")
        raise HTTPException(status_code=500, detail="Decryption failed")


@router.post("/hash")
async def hash_text(
    request: HashRequest,
    user: User = Depends(get_current_user)
):
    """Хеширование текста с использованием Стрибог-512"""
    try:
        hash_service = HashService()
        hash_result = hash_service.hash_text(request.text)

        logger.info(f"User {user.username} hashed text with Streebog-512")

        return {"hash": hash_result}
    except Exception as e:
        logger.error(f"Error during hashing: {str(e)}")
        raise HTTPException(status_code=500, detail="Hashing failed")


@router.get("/keys")
async def list_keys(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение списка RSA ключей пользователя"""
    rsa_service = RSAService()
    keys = rsa_service.list_user_keys(user.id, db)

    return {"keys": keys}


@router.delete("/keys/{key_id}")
async def delete_key(
    key_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Удаление RSA ключа"""
    try:
        rsa_service = RSAService()
        rsa_service.delete_key(key_id, user.id, db)

        return {"message": "Key deleted successfully"}
    except ValueError as e:
        logger.error(f"Error deleting key: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
