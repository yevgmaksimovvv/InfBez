"""
Сервис для RSA шифрования/расшифрования с управлением ключами
"""
import logging
import uuid
from sqlalchemy.orm import Session
from gmpy2 import mpz

from algorithms.rsa_32768 import RSA32768
from backend.models import RSAKeyPair, User
from backend.core.encryption import get_key_encryption
from backend.config import settings

logger = logging.getLogger(__name__)


class RSAService:
    """Сервис для работы с RSA-32768"""

    @staticmethod
    def validate_text_size(text_bytes: bytes) -> None:
        """
        Валидация размера текста для RSA

        Args:
            text_bytes: Текст в байтах

        Raises:
            ValueError: Если текст слишком длинный
        """
        if len(text_bytes) > settings.MAX_RSA_BLOCK:
            raise ValueError(
                f"Text too long for RSA-32768 (max {settings.MAX_RSA_BLOCK} bytes)"
            )

    @staticmethod
    def check_user_keys_limit(db: Session, user_id: int) -> None:
        """
        Проверка лимита ключей пользователя

        Args:
            db: Database session
            user_id: ID пользователя

        Raises:
            ValueError: Если превышен лимит ключей
        """
        user_keys_count = db.query(RSAKeyPair).filter(
            RSAKeyPair.user_id == user_id
        ).count()

        if user_keys_count >= settings.MAX_RSA_KEYS_PER_USER:
            raise ValueError(
                f"Maximum RSA keys limit reached ({settings.MAX_RSA_KEYS_PER_USER})"
            )

    def encrypt(self, text: str, user: User, db: Session) -> dict:
        """
        Шифрует текст с использованием RSA и сохраняет ключи

        Args:
            text: Текст для шифрования
            user: Пользователь
            db: Database session

        Returns:
            dict: {encrypted_hex, key_id, public_key}

        Raises:
            ValueError: Если текст слишком длинный или превышен лимит ключей
        """
        text_bytes = text.encode('utf-8')
        self.validate_text_size(text_bytes)
        self.check_user_keys_limit(db, user.id)

        # Генерация новой пары ключей RSA-32768
        logger.info(f"Generating RSA keypair for user {user.username}...")
        rsa = RSA32768()

        # Шифрование текста с использованием открытого ключа
        encrypted = rsa.encrypt(text_bytes)

        # Генерация уникального идентификатора для пары ключей
        key_id = str(uuid.uuid4())

        # Шифрование приватного ключа перед сохранением в базу данных
        key_enc = get_key_encryption()
        encrypted_d = key_enc.encrypt_key(str(rsa.private_key))

        # Сохранение пары ключей в базе данных
        keypair = RSAKeyPair(
            user_id=user.id,
            key_id=key_id,
            p=str(rsa.p),
            q=str(rsa.q),
            n=str(rsa.n),
            e=str(rsa.public_key),
            d=encrypted_d
        )
        db.add(keypair)
        db.commit()

        logger.info(f"User {user.username} encrypted text with RSA-32768, key_id: {key_id}")

        return {
            "encrypted": encrypted.hex(),
            "key_id": key_id,
            "public_key": str(rsa.public_key)
        }

    def decrypt(self, encrypted_hex: str, key_id: str, user: User, db: Session) -> str:
        """
        Расшифровывает текст с использованием сохраненных RSA ключей

        Args:
            encrypted_hex: Зашифрованный текст в hex
            key_id: ID ключа
            user: Пользователь
            db: Database session

        Returns:
            str: Расшифрованный текст

        Raises:
            ValueError: Если ключ не найден или данные некорректны
        """
        # Получение пары ключей из базы данных
        keypair = db.query(RSAKeyPair).filter(
            RSAKeyPair.key_id == key_id,
            RSAKeyPair.user_id == user.id
        ).first()

        if not keypair:
            raise ValueError("RSA keypair not found")

        # Расшифрование приватного ключа из зашифрованного хранилища
        key_enc = get_key_encryption()
        decrypted_d = key_enc.decrypt_key(keypair.d)

        # Восстановление объекта RSA-32768 из сохраненных параметров
        rsa = RSA32768(
            p=mpz(keypair.p),
            q=mpz(keypair.q),
            n=mpz(keypair.n),
            e=mpz(keypair.e),
            d=mpz(decrypted_d)
        )

        # Проверка корректности зашифрованных данных
        try:
            cipher_bytes = bytes.fromhex(encrypted_hex)
        except ValueError:
            raise ValueError("Invalid encrypted data format")

        if len(cipher_bytes) != 4096:
            raise ValueError("Invalid RSA ciphertext length")

        # Расшифрование данных с использованием приватного ключа
        decrypted = rsa.decrypt(cipher_bytes)

        logger.info(f"User {user.username} decrypted text with RSA-32768, key_id: {key_id}")

        return decrypted.decode('utf-8')

    def list_user_keys(self, user_id: int, db: Session) -> list[dict]:
        """
        Получение списка пар ключей пользователя

        Args:
            user_id: ID пользователя
            db: Database session

        Returns:
            list: Список пар ключей
        """
        keypairs = db.query(RSAKeyPair).filter(RSAKeyPair.user_id == user_id).all()

        return [
            {
                "key_id": kp.key_id,
                "created_at": kp.created_at.isoformat(),
                "public_key": kp.e
            }
            for kp in keypairs
        ]

    def delete_key(self, key_id: str, user_id: int, db: Session) -> None:
        """
        Удаление пары ключей

        Args:
            key_id: Идентификатор ключа
            user_id: ID пользователя
            db: Database session

        Raises:
            ValueError: Если ключ не найден
        """
        # Проверка корректности формата идентификатора
        try:
            uuid.UUID(key_id)
        except ValueError:
            raise ValueError("Invalid key_id format")

        keypair = db.query(RSAKeyPair).filter(
            RSAKeyPair.key_id == key_id,
            RSAKeyPair.user_id == user_id
        ).first()

        if not keypair:
            raise ValueError("Key not found")

        db.delete(keypair)
        db.commit()

        logger.info(f"User {user_id} deleted RSA key {key_id}")
