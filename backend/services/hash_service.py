"""
Сервис для хеширования с использованием Стрибог-512
"""
import logging
from algorithms.streebog.streebog import streebog_512

logger = logging.getLogger(__name__)


class HashService:
    """Сервис для хеширования с использованием Streebog-512"""

    @staticmethod
    def hash_text(text: str) -> str:
        """
        Хеширует текст с использованием Стрибог-512

        Args:
            text: Текст для хеширования

        Returns:
            str: Хеш в шестнадцатеричном формате
        """
        hash_result = streebog_512(text.encode('utf-8'))
        logger.debug(f"Hashed text with Streebog-512 ({len(text)} chars)")
        return hash_result.hex()
