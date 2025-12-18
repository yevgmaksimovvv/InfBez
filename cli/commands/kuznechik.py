"""
Команды для шифрования Кузнечик (ГОСТ Р 34.12-2018)
"""

import typer
from pathlib import Path
from typing import Optional

from cli.utils import (
    console, print_success, print_error,
    encode_data, decode_data, load_json_file, save_json_file,
    read_input_data, get_timestamp, format_bytes
)
from cli.services.crypto_service import KuznechikService
from cli.exit_codes import ExitCode

app = typer.Typer(help="Шифрование Кузнечик (ГОСТ Р 34.12-2018)")


@app.command("encrypt")
def encrypt(
    input_data: str = typer.Argument(..., help="Текст или путь к файлу"),
    output: Optional[Path] = typer.Option(
        None,
        "--output", "-o",
        help="Путь для сохранения (по умолчанию: encrypted.json)"
    ),
    force_file: bool = typer.Option(
        False,
        "--file",
        help="Принудительно читать как файл (игнорировать автоопределение)"
    ),
    force_text: bool = typer.Option(
        False,
        "--text",
        help="Принудительно читать как текст (игнорировать автоопределение)"
    ),
    force: bool = typer.Option(
        False,
        "--force", "-f",
        help="Перезаписать файл если существует"
    ),
):
    """
    Шифрование данных алгоритмом Кузнечик

    Примеры:

      kuznechik encrypt "Секретное сообщение"
      kuznechik encrypt document.txt -o encrypted.json
      kuznechik encrypt "README.md" --text  # Зашифровать текст "README.md"
      kuznechik encrypt README.md --file    # Зашифровать файл README.md
    """
    try:
        # Чтение с учетом флагов
        data = read_input_data(input_data, force_file=force_file, force_text=force_text)

        # Валидация размера (макс. 1MB)
        if len(data) > 1024 * 1024:
            print_error(f"Файл слишком большой: {format_bytes(len(data))} (макс. 1MB)")
            raise typer.Exit(code=ExitCode.DATA_TOO_LARGE)

        # Шифрование
        encrypted_data, key = KuznechikService.encrypt(data)

        # Формирование результата
        result = {
            "encrypted": encode_data(encrypted_data, 'base64'),
            "key": encode_data(key, 'base64'),
            "algorithm": "kuznechik",
            "encoding": "base64",
            "original_size": len(data),
            "encrypted_size": len(encrypted_data),
            "timestamp": get_timestamp()
        }

        # Сохранение
        if output is None:
            output = Path("encrypted.json")

        # Проверка перезаписи
        if output.exists() and not force:
            print_error(f"Файл {output} уже существует. Используйте --force для перезаписи")
            raise typer.Exit(code=ExitCode.FILE_WRITE_ERROR)

        save_json_file(result, output)
        print_success(f"Зашифровано: {format_bytes(len(data))} → {format_bytes(len(encrypted_data))}")
        console.print(f"Сохранено в [cyan]{output}[/cyan]")

    except FileNotFoundError as e:
        print_error(f"Файл не найден: {e}")
        raise typer.Exit(code=ExitCode.FILE_NOT_FOUND)
    except ValueError as e:
        print_error(f"Ошибка: {e}")
        raise typer.Exit(code=ExitCode.INVALID_INPUT)
    except Exception as e:
        print_error(f"Ошибка шифрования: {e}")
        raise typer.Exit(code=ExitCode.ENCRYPTION_ERROR)


@app.command("decrypt")
def decrypt(
    input_file: Path = typer.Argument(..., help="Файл с зашифрованными данными (JSON)"),
    output: Optional[Path] = typer.Option(
        None,
        "--output", "-o",
        help="Путь для сохранения результата"
    ),
    key_file: Optional[Path] = typer.Option(
        None,
        "--key", "-k",
        help="Путь к файлу с ключом (если ключ не в input_file)"
    ),
    force: bool = typer.Option(
        False,
        "--force", "-f",
        help="Перезаписать файл если существует"
    ),
):
    """
    Расшифрование данных алгоритмом Кузнечик

    Примеры:

      kuznechik decrypt encrypted.json
      kuznechik decrypt encrypted.json -o decrypted.txt
      kuznechik decrypt data.json --key separate_key.json
    """
    try:
        # Загрузка зашифрованных данных
        encrypted_obj = load_json_file(input_file)
        encrypted_data = decode_data(
            encrypted_obj['encrypted'],
            encrypted_obj.get('encoding', 'base64')
        )

        # Загрузка ключа
        if 'key' in encrypted_obj:
            # Ключ в том же файле
            key = decode_data(encrypted_obj['key'], encrypted_obj.get('encoding', 'base64'))
        elif key_file:
            # Ключ в отдельном файле
            key_obj = load_json_file(key_file)
            key = decode_data(key_obj['key'], key_obj.get('encoding', 'base64'))
        else:
            print_error("Ключ не найден ни в input_file, ни в --key")
            raise typer.Exit(code=ExitCode.INVALID_KEY)

        # Расшифрование
        decrypted_data = KuznechikService.decrypt(encrypted_data, key)

        # Вывод результата
        if output:
            # Проверка перезаписи
            if output.exists() and not force:
                print_error(f"Файл {output} уже существует. Используйте --force для перезаписи")
                raise typer.Exit(code=ExitCode.FILE_WRITE_ERROR)

            with open(output, 'wb') as f:
                f.write(decrypted_data)
            print_success(f"Расшифровано: {format_bytes(len(decrypted_data))}")
            console.print(f"Сохранено в [cyan]{output}[/cyan]")
        else:
            # Вывод в stdout
            try:
                console.print(decrypted_data.decode('utf-8'))
            except UnicodeDecodeError:
                print_error("Бинарные данные - используйте --output для сохранения")
                raise typer.Exit(code=ExitCode.INVALID_FORMAT)

    except FileNotFoundError as e:
        print_error(f"Файл не найден: {e}")
        raise typer.Exit(code=ExitCode.FILE_NOT_FOUND)
    except KeyError as e:
        print_error(f"Некорректный формат файла: отсутствует поле {e}")
        raise typer.Exit(code=ExitCode.INVALID_FORMAT)
    except Exception as e:
        print_error(f"Ошибка расшифрования: {e}")
        raise typer.Exit(code=ExitCode.DECRYPTION_ERROR)


if __name__ == "__main__":
    app()
