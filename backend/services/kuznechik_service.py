"""
Сервис для шифрования/расшифрования с использованием Кузнечик
"""
import logging
from algorithms.kuznechik.kuznechik import Kuznechik
from backend.config import settings

logger = logging.getLogger(__name__)


class KuznechikService:
    """Сервис для работы с алгоритмом Кузнечик"""

    @staticmethod
    def add_pkcs7_padding(data: bytes) -> bytes:
        """
        Добавляет PKCS#7 padding к данным

        Args:
            data: Данные для padding

        Returns:
            bytes: Данные с padding
        """
        padding_length = 16 - (len(data) % 16)
        return data + bytes([padding_length] * padding_length)

    @staticmethod
    def remove_pkcs7_padding(data: bytes) -> bytes:
        """
        Удаляет и валидирует PKCS#7 padding

        Args:
            data: Данные с padding

        Returns:
            bytes: Данные без padding

        Raises:
            ValueError: Если padding некорректный
        """
        if len(data) == 0:
            raise ValueError("Empty data")

        padding_length = data[-1]

        if padding_length == 0 or padding_length > 16:
            raise ValueError("Invalid padding length")

        padding_bytes = data[-padding_length:]
        if not all(b == padding_length for b in padding_bytes):
            raise ValueError("Invalid padding bytes")

        return data[:-padding_length]

    @staticmethod
    def validate_text_size(text_bytes: bytes) -> None:
        """
        Валидация размера текста для Кузнечика

        Args:
            text_bytes: Текст в байтах

        Raises:
            ValueError: Если текст слишком длинный
        """
        if len(text_bytes) > settings.MAX_KUZNECHIK_BLOCK:
            raise ValueError(
                f"Text too long for Kuznechik (max {settings.MAX_KUZNECHIK_BLOCK} bytes)"
            )

    def encrypt(self, text: str) -> tuple[str, str]:
        """
        Шифрует текст с использованием Кузнечика

        Args:
            text: Текст для шифрования

        Returns:
            tuple: (encrypted_hex, key_hex)

        Raises:
            ValueError: Если текст слишком длинный
        """
        text_bytes = text.encode('utf-8')
        self.validate_text_size(text_bytes)

        # Генерация ключа
        kuz = Kuznechik()
        key = kuz.keys[0].hex()

        # Добавление PKCS#7 padding
        text_bytes = self.add_pkcs7_padding(text_bytes)

        # Шифрование блоками по 16 байт
        encrypted_blocks = []
        for i in range(0, len(text_bytes), 16):
            block = text_bytes[i:i + 16]
            encrypted_block = kuz.encrypt(block)
            encrypted_blocks.append(encrypted_block.hex())

        encrypted_hex = "".join(encrypted_blocks)

        logger.debug(f"Kuznechik encrypted {len(text_bytes)} bytes")

        return encrypted_hex, key

    def decrypt(self, encrypted_hex: str, key_hex: str) -> str:
        """
        Расшифровывает текст с использованием Кузнечика

        Args:
            encrypted_hex: Зашифрованный текст в hex
            key_hex: Ключ в hex

        Returns:
            str: Расшифрованный текст

        Raises:
            ValueError: Если ключ или данные некорректны
        """
        # Валидация ключа
        try:
            key_bytes = bytes.fromhex(key_hex)
            if len(key_bytes) != 32:
                raise ValueError("Invalid key length")
        except ValueError:
            raise ValueError("Invalid key format")

        # Валидация зашифрованных данных
        try:
            encrypted_bytes = bytes.fromhex(encrypted_hex)
        except ValueError:
            raise ValueError("Invalid encrypted data format")

        if len(encrypted_bytes) % 16 != 0:
            raise ValueError("Invalid encrypted data length")

        # Инициализация Кузнечика с ключом
        kuz = Kuznechik(key=key_bytes)

        # Расшифрование блоками
        decrypted_blocks = []
        for i in range(0, len(encrypted_bytes), 16):
            block = encrypted_bytes[i:i + 16]
            decrypted_block = kuz.decrypt(block)
            decrypted_blocks.append(decrypted_block)

        decrypted = b"".join(decrypted_blocks)

        # Удаление padding с валидацией
        try:
            decrypted = self.remove_pkcs7_padding(decrypted)
        except ValueError as e:
            logger.error(f"Padding validation failed: {e}")
            raise ValueError("Decryption failed - invalid padding")

        logger.debug(f"Kuznechik decrypted {len(decrypted)} bytes")

        return decrypted.decode('utf-8')
