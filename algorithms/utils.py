"""
Утилиты для работы с алгоритмами
"""


def hex_to_bytes(hex_str: str) -> bytes:
    """
    Перевод шестнадцатеричных чисел в байты
    """
    return bytes.fromhex(hex_str.replace(' ', ''))


def bytes_to_hex(data: bytes) -> str:
    """
    Перевод байтов в шестнадцатеричную строку
    """
    return data.hex().upper()


def random_bytes(length: int) -> bytes:
    """
    Генерация случайных байтов
    """
    import os
    return os.urandom(length)

