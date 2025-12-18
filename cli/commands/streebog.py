"""
Команды для хеширования Стрибог-512 (ГОСТ 34.11-2018)
"""

import typer
from pathlib import Path
from typing import Optional

from cli.utils import (
    console, print_success, print_error,
    encode_data, read_input_data, format_bytes
)
from cli.services.crypto_service import StreebogService
from cli.exit_codes import ExitCode

app = typer.Typer(help="Хеширование Стрибог-512 (ГОСТ 34.11-2018)")


@app.command("hash")
def hash_data(
    input_data: str = typer.Argument(..., help="Текст или путь к файлу"),
    hex_output: bool = typer.Option(
        True,
        "--hex/--base64",
        help="Формат вывода (hex по умолчанию)"
    ),
    force_file: bool = typer.Option(
        False,
        "--file",
        help="Принудительно читать как файл"
    ),
    force_text: bool = typer.Option(
        False,
        "--text",
        help="Принудительно читать как текст"
    ),
):
    """
    Хеширование данных алгоритмом Стрибог-512

    Примеры:

      streebog hash "Hello, World!"
      streebog hash document.pdf
      streebog hash file.txt --base64
    """
    try:
        # Чтение с учетом флагов
        data = read_input_data(input_data, force_file=force_file, force_text=force_text)
        is_file = Path(input_data).exists() and not force_text

        # Хеширование
        hash_bytes = StreebogService.hash(data)

        # Форматирование
        encoding = 'hex' if hex_output else 'base64'
        hash_str = encode_data(hash_bytes, encoding)

        # Вывод
        if is_file:
            console.print(f"[cyan]{Path(input_data).name}[/cyan]")
            console.print(f"  Размер: {format_bytes(len(data))}")
            console.print(f"  Хеш:    [green]{hash_str}[/green]")
        else:
            console.print(hash_str)

    except FileNotFoundError as e:
        print_error(f"Файл не найден: {e}")
        raise typer.Exit(code=ExitCode.FILE_NOT_FOUND)
    except Exception as e:
        print_error(f"Ошибка хеширования: {e}")
        raise typer.Exit(code=ExitCode.HASH_ERROR)


@app.command("verify")
def verify_hash(
    input_data: str = typer.Argument(..., help="Текст или путь к файлу"),
    expected_hash: str = typer.Argument(..., help="Ожидаемый хеш"),
    hex_input: bool = typer.Option(
        True,
        "--hex/--base64",
        help="Формат входного хеша"
    ),
    force_file: bool = typer.Option(
        False,
        "--file",
        help="Принудительно читать как файл"
    ),
    force_text: bool = typer.Option(
        False,
        "--text",
        help="Принудительно читать как текст"
    ),
):
    """
    Проверка хеша Стрибог-512

    Примеры:

      streebog verify document.pdf "9a8b7c6d..."
      streebog verify "Hello" "abc123..." --base64
    """
    try:
        # Чтение с учетом флагов
        data = read_input_data(input_data, force_file=force_file, force_text=force_text)
        is_file = Path(input_data).exists() and not force_text

        # Проверка
        encoding = 'hex' if hex_input else 'base64'
        is_valid = StreebogService.verify(data, expected_hash, encoding)

        if is_valid:
            print_success("✓ Хеш совпадает")
            if is_file:
                console.print(f"Файл: [cyan]{input_data}[/cyan]")
            console.print(f"Хеш:  [green]{expected_hash}[/green]")
        else:
            print_error("✗ Хеш НЕ совпадает")

            # Показываем актуальный хеш
            actual_hash = StreebogService.hash(data)
            actual_hash_str = encode_data(actual_hash, encoding)

            console.print(f"  Ожидалось: [dim]{expected_hash}[/dim]")
            console.print(f"  Получено:  [red]{actual_hash_str}[/red]")
            raise typer.Exit(code=ExitCode.HASH_ERROR)

    except FileNotFoundError as e:
        print_error(f"Файл не найден: {e}")
        raise typer.Exit(code=ExitCode.FILE_NOT_FOUND)
    except Exception as e:
        print_error(f"Ошибка проверки: {e}")
        raise typer.Exit(code=ExitCode.HASH_ERROR)


if __name__ == "__main__":
    app()
