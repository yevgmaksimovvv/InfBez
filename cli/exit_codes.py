"""
Стандартизированные коды выхода для CLI
"""

from enum import IntEnum


class ExitCode(IntEnum):
    """Коды выхода для CLI команд"""

    SUCCESS = 0

    # Ошибки файловой системы (1-9)
    FILE_NOT_FOUND = 1
    FILE_READ_ERROR = 2
    FILE_WRITE_ERROR = 3

    # Ошибки валидации (10-19)
    INVALID_INPUT = 10
    INVALID_KEY = 11
    INVALID_FORMAT = 12
    DATA_TOO_LARGE = 13

    # Криптографические ошибки (20-29)
    ENCRYPTION_ERROR = 20
    DECRYPTION_ERROR = 21
    HASH_ERROR = 22
    KEY_GENERATION_ERROR = 23

    # Ошибки зависимостей (30-39)
    MISSING_DEPENDENCY = 30
    GMPY2_NOT_AVAILABLE = 31

    # Общие ошибки (40+)
    OPERATION_CANCELLED = 40
    UNKNOWN_ERROR = 99


def exit_with_code(code: ExitCode, message: str = None):
    """
    Выход с определенным кодом и опциональным сообщением

    Args:
        code: Код выхода из ExitCode enum
        message: Опциональное сообщение для вывода
    """
    import typer
    from cli.utils import print_error

    if message:
        print_error(message)

    raise typer.Exit(code=code.value)
