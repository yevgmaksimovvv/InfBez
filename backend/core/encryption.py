"""
Утилиты шифрования для приватных RSA ключей
Использует Fernet (симметричное шифрование) с мастер-ключом
"""
from cryptography.fernet import Fernet
import logging

from backend.config import settings

logger = logging.getLogger(__name__)


class KeyEncryption:
    """
    Класс для шифрования/расшифрования приватных RSA ключей
    """

    def __init__(self):
        """
        Инициализация с мастер-ключом из переменных окружения
        """
        master_key = settings.MASTER_KEY

        if not master_key:
            logger.warning("MASTER_KEY not found in environment, generating temporary key")
            logger.warning("THIS IS INSECURE! Set MASTER_KEY in .env for production")
            master_key = Fernet.generate_key().decode()

        try:
            if isinstance(master_key, str):
                master_key = master_key.encode()
            self.fernet = Fernet(master_key)
        except Exception as e:
            logger.error(f"Invalid MASTER_KEY format: {e}")
            raise ValueError(
                "Invalid MASTER_KEY. Generate new one with: "
                "python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
            )

    def encrypt_key(self, private_key: str) -> str:
        """
        Шифрует приватный ключ

        Args:
            private_key: Приватный ключ в виде строки

        Returns:
            Зашифрованный ключ в виде строки (base64)
        """
        try:
            key_bytes = private_key.encode() if isinstance(private_key, str) else private_key
            encrypted = self.fernet.encrypt(key_bytes)
            return encrypted.decode()
        except Exception as e:
            logger.error(f"Error encrypting key: {e}")
            raise

    def decrypt_key(self, encrypted_key: str) -> str:
        """
        Расшифровывает приватный ключ

        Args:
            encrypted_key: Зашифрованный ключ в виде строки (base64)

        Returns:
            Расшифрованный ключ в виде строки
        """
        try:
            encrypted_bytes = encrypted_key.encode() if isinstance(encrypted_key, str) else encrypted_key
            decrypted = self.fernet.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Error decrypting key: {e}")
            raise


# Singleton экземпляр
_key_encryption = None


def get_key_encryption() -> KeyEncryption:
    """
    Получает экземпляр KeyEncryption (singleton)
    """
    global _key_encryption
    if _key_encryption is None:
        _key_encryption = KeyEncryption()
    return _key_encryption


def generate_master_key() -> str:
    """
    Генерирует новый мастер-ключ

    Returns:
        Мастер-ключ в виде строки (base64)
    """
    return Fernet.generate_key().decode()
