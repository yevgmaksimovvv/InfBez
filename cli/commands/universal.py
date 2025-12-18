"""
Универсальные команды для быстрого доступа
"""

import typer
from pathlib import Path
from typing import Optional

from cli.utils import (
    console, print_success, print_error, print_warning, print_info,
    encode_data, decode_data, load_json_file, save_json_file,
    read_input_data, get_timestamp, format_bytes
)
from cli.services.crypto_service import KuznechikService, StreebogService
from cli.exit_codes import ExitCode


def encrypt_universal():
    """
    Универсальное шифрование (использует Кузнечик)

    Примеры:
      encrypt "text"
      encrypt file.txt -o encrypted.json
    """
    import sys

    # Парсинг аргументов вручную для совместимости с entry point
    args = sys.argv[1:]

    if not args or args[0] in ['-h', '--help']:
        console.print("[bold]Универсальное шифрование (Кузнечик)[/bold]\n")
        console.print("Использование: encrypt <данные> [опции]\n")
        console.print("Аргументы:")
        console.print("  <данные>          Текст или путь к файлу\n")
        console.print("Опции:")
        console.print("  -o, --output PATH Путь для сохранения (по умолчанию: encrypted.json)")
        console.print("  --file            Принудительно читать как файл")
        console.print("  --text            Принудительно читать как текст")
        console.print("  -h, --help        Показать справку")
        return

    # Простой парсинг
    input_data = args[0]
    output = None
    force_file = '--file' in args
    force_text = '--text' in args

    if '-o' in args:
        idx = args.index('-o')
        output = Path(args[idx + 1]) if idx + 1 < len(args) else None
    elif '--output' in args:
        idx = args.index('--output')
        output = Path(args[idx + 1]) if idx + 1 < len(args) else None

    try:
        # Чтение данных
        data = read_input_data(input_data, force_file=force_file, force_text=force_text)

        # Валидация размера
        if len(data) > 1024 * 1024:
            print_error(f"Файл слишком большой: {format_bytes(len(data))} (макс. 1MB)")
            sys.exit(ExitCode.DATA_TOO_LARGE)

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
        if output.exists():
            if '--force' not in args and '-f' not in args:
                print_warning(f"Файл {output} уже существует. Используйте --force для перезаписи")
                sys.exit(ExitCode.FILE_WRITE_ERROR)

        save_json_file(result, output)
        print_success(f"Зашифровано: {format_bytes(len(data))} → {format_bytes(len(encrypted_data))}")
        console.print(f"Сохранено в [cyan]{output}[/cyan]")

    except FileNotFoundError as e:
        print_error(f"Файл не найден: {e}")
        sys.exit(ExitCode.FILE_NOT_FOUND)
    except Exception as e:
        print_error(f"Ошибка шифрования: {e}")
        sys.exit(ExitCode.ENCRYPTION_ERROR)


def decrypt_universal():
    """
    Универсальное расшифрование (автоопределение алгоритма)

    Примеры:
      decrypt encrypted.json
      decrypt encrypted.json -o decrypted.txt
    """
    import sys

    args = sys.argv[1:]

    if not args or args[0] in ['-h', '--help']:
        console.print("[bold]Универсальное расшифрование[/bold]\n")
        console.print("Использование: decrypt <файл> [опции]\n")
        console.print("Аргументы:")
        console.print("  <файл>            Файл с зашифрованными данными (JSON)\n")
        console.print("Опции:")
        console.print("  -o, --output PATH Путь для сохранения результата")
        console.print("  -k, --key PATH    Путь к файлу с ключом")
        console.print("  -h, --help        Показать справку")
        return

    input_file = Path(args[0])
    output = None
    key_file = None

    if '-o' in args:
        idx = args.index('-o')
        output = Path(args[idx + 1]) if idx + 1 < len(args) else None
    elif '--output' in args:
        idx = args.index('--output')
        output = Path(args[idx + 1]) if idx + 1 < len(args) else None

    if '-k' in args:
        idx = args.index('-k')
        key_file = Path(args[idx + 1]) if idx + 1 < len(args) else None
    elif '--key' in args:
        idx = args.index('--key')
        key_file = Path(args[idx + 1]) if idx + 1 < len(args) else None

    try:
        # Загрузка зашифрованных данных
        encrypted_obj = load_json_file(input_file)
        encrypted_data = decode_data(
            encrypted_obj['encrypted'],
            encrypted_obj.get('encoding', 'base64')
        )

        # Загрузка ключа
        if 'key' in encrypted_obj:
            key = decode_data(encrypted_obj['key'], encrypted_obj.get('encoding', 'base64'))
        elif key_file:
            key_obj = load_json_file(key_file)
            key = decode_data(key_obj['key'], key_obj.get('encoding', 'base64'))
        else:
            print_error("Ключ не найден ни в input_file, ни в --key")
            sys.exit(ExitCode.INVALID_KEY)

        # Расшифрование (используем Кузнечик по умолчанию)
        decrypted_data = KuznechikService.decrypt(encrypted_data, key)

        # Вывод результата
        if output:
            # Проверка перезаписи
            if output.exists():
                if '--force' not in args and '-f' not in args:
                    print_warning(f"Файл {output} уже существует. Используйте --force для перезаписи")
                    sys.exit(ExitCode.FILE_WRITE_ERROR)

            with open(output, 'wb') as f:
                f.write(decrypted_data)
            print_success(f"Расшифровано: {format_bytes(len(decrypted_data))}")
            console.print(f"Сохранено в [cyan]{output}[/cyan]")
        else:
            try:
                console.print(decrypted_data.decode('utf-8'))
            except UnicodeDecodeError:
                print_error("Бинарные данные - используйте --output для сохранения")
                sys.exit(ExitCode.INVALID_FORMAT)

    except FileNotFoundError as e:
        print_error(f"Файл не найден: {e}")
        sys.exit(ExitCode.FILE_NOT_FOUND)
    except KeyError as e:
        print_error(f"Некорректный формат файла: отсутствует поле {e}")
        sys.exit(ExitCode.INVALID_FORMAT)
    except Exception as e:
        print_error(f"Ошибка расшифрования: {e}")
        sys.exit(ExitCode.DECRYPTION_ERROR)


def hash_universal():
    """
    Универсальное хеширование (использует Стрибог-512)

    Примеры:
      hash "text"
      hash file.pdf
    """
    import sys

    args = sys.argv[1:]

    if not args or args[0] in ['-h', '--help']:
        console.print("[bold]Универсальное хеширование (Стрибог-512)[/bold]\n")
        console.print("Использование: hash <данные> [опции]\n")
        console.print("Аргументы:")
        console.print("  <данные>          Текст или путь к файлу\n")
        console.print("Опции:")
        console.print("  --hex             Вывод в hex (по умолчанию)")
        console.print("  --base64          Вывод в base64")
        console.print("  --file            Принудительно читать как файл")
        console.print("  --text            Принудительно читать как текст")
        console.print("  -h, --help        Показать справку")
        return

    input_data = args[0]
    hex_output = '--base64' not in args
    force_file = '--file' in args
    force_text = '--text' in args

    try:
        # Чтение данных
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
        sys.exit(ExitCode.FILE_NOT_FOUND)
    except Exception as e:
        print_error(f"Ошибка хеширования: {e}")
        sys.exit(ExitCode.HASH_ERROR)


if __name__ == "__main__":
    pass
