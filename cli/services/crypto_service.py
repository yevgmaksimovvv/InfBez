"""
Сервис для криптографических операций
Вынесена вся бизнес-логика из команд CLI
"""

import os
from pathlib import Path
from typing import Optional, Tuple

from algorithms.kuznechik.kuznechik import Kuznechik
from algorithms.streebog.streebog import streebog_512


class KuznechikService:
    """Сервис для работы с алгоритмом Кузнечик"""

    BLOCK_SIZE = 16
    KEY_SIZE = 32  # 256 bits

    @staticmethod
    def encrypt(data: bytes, key: Optional[bytes] = None) -> Tuple[bytes, bytes]:
        """
        Шифрование данных алгоритмом Кузнечик

        Args:
            data: Данные для шифрования
            key: Ключ шифрования (если None, генерируется новый)

        Returns:
            (encrypted_data, key) - зашифрованные данные и ключ
        """
        if key is None:
            key = os.urandom(KuznechikService.KEY_SIZE)

        cipher = Kuznechik(key)

        # PKCS#7 padding
        padding_length = KuznechikService.BLOCK_SIZE - (len(data) % KuznechikService.BLOCK_SIZE)
        padded_data = data + bytes([padding_length] * padding_length)

        # Шифрование блоками
        encrypted_blocks = []
        for i in range(0, len(padded_data), KuznechikService.BLOCK_SIZE):
            block = padded_data[i:i + KuznechikService.BLOCK_SIZE]
            encrypted_block = cipher.encrypt(block)
            encrypted_blocks.append(encrypted_block)

        encrypted_data = b''.join(encrypted_blocks)
        return encrypted_data, key

    @staticmethod
    def decrypt(encrypted_data: bytes, key: bytes) -> bytes:
        """
        Расшифрование данных алгоритмом Кузнечик

        Args:
            encrypted_data: Зашифрованные данные
            key: Ключ расшифрования

        Returns:
            Расшифрованные данные
        """
        cipher = Kuznechik(key)

        # Расшифрование блоками
        decrypted_blocks = []
        for i in range(0, len(encrypted_data), KuznechikService.BLOCK_SIZE):
            block = encrypted_data[i:i + KuznechikService.BLOCK_SIZE]
            decrypted_block = cipher.decrypt(block)
            decrypted_blocks.append(decrypted_block)

        decrypted_data = b''.join(decrypted_blocks)

        # Удаление PKCS#7 padding
        padding_length = decrypted_data[-1]
        return decrypted_data[:-padding_length]


class RSAService:
    """Сервис для работы с RSA-32768"""

    MAX_DATA_SIZE = 4090  # байт

    @staticmethod
    def encrypt(data: bytes, public_key: dict) -> bytes:
        """
        Шифрование данных RSA-32768

        Args:
            data: Данные для шифрования (макс. 4090 байт)
            public_key: Публичный ключ {'n': int, 'e': int}

        Returns:
            Зашифрованные данные
        """
        from algorithms.rsa_32768 import RSA32768

        if len(data) > RSAService.MAX_DATA_SIZE:
            raise ValueError(f"Данные слишком большие: {len(data)} байт (макс. {RSAService.MAX_DATA_SIZE})")

        rsa = RSA32768(public_key=public_key)
        return rsa.encrypt(data)

    @staticmethod
    def decrypt(encrypted_data: bytes, public_key: dict, private_key: dict) -> bytes:
        """
        Расшифрование данных RSA-32768

        Args:
            encrypted_data: Зашифрованные данные
            public_key: Публичный ключ
            private_key: Приватный ключ

        Returns:
            Расшифрованные данные
        """
        from algorithms.rsa_32768 import RSA32768

        rsa = RSA32768(public_key=public_key, private_key=private_key)
        return rsa.decrypt(encrypted_data)


class StreebogService:
    """Сервис для работы с хешированием Стрибог-512"""

    @staticmethod
    def hash(data: bytes) -> bytes:
        """
        Хеширование данных алгоритмом Стрибог-512

        Args:
            data: Данные для хеширования

        Returns:
            Хеш (64 байта)
        """
        return streebog_512(data)

    @staticmethod
    def verify(data: bytes, expected_hash: str, encoding: str = 'hex') -> bool:
        """
        Проверка хеша

        Args:
            data: Данные для проверки
            expected_hash: Ожидаемый хеш (строка)
            encoding: Кодировка хеша ('hex' или 'base64')

        Returns:
            True если хеш совпадает
        """
        actual_hash = StreebogService.hash(data)

        # Преобразование в строку
        if encoding == 'hex':
            actual_hash_str = actual_hash.hex()
        elif encoding == 'base64':
            import base64
            actual_hash_str = base64.b64encode(actual_hash).decode('ascii')
        else:
            raise ValueError(f"Неизвестная кодировка: {encoding}")

        return actual_hash_str.lower() == expected_hash.lower()
