"""
Команды для криптографических операций
"""

import typer
from enum import Enum
from pathlib import Path
from typing import Optional
import os
import sys

# Добавляем путь к корню проекта для импорта algorithms
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Ленивый импорт для избежания ошибок с зависимостями при старте CLI
# from algorithms.kuznechik.kuznechik import Kuznechik
# from algorithms.streebog.streebog import Streebog
# from algorithms.rsa_32768 import RSA32768
from cli.utils import (
    console, print_success, print_error, print_warning,
    encode_data, decode_data, load_json_file, save_json_file,
    read_file_or_text, write_output, validate_data_size,
    get_timestamp, format_bytes
)

app = typer.Typer(help="Криптографические операции")


class Algorithm(str, Enum):
    """Поддерживаемые алгоритмы шифрования"""
    kuznechik = "kuznechik"
    rsa = "rsa"


class Encoding(str, Enum):
    """Поддерживаемые кодировки"""
    base64 = "base64"
    hex = "hex"


@app.command("encrypt")
def encrypt(
    input_data: str = typer.Argument(..., help="Текст для шифрования или путь к файлу (с --file)"),
    algorithm: Algorithm = typer.Option(
        Algorithm.kuznechik,
        "--algorithm", "-a",
        help="Алгоритм шифрования"
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output", "-o",
        help="Путь для сохранения результата (по умолчанию: stdout)"
    ),
    is_file: bool = typer.Option(
        False,
        "--file", "-f",
        help="INPUT - путь к файлу, а не текст"
    ),
    key_file: Optional[Path] = typer.Option(
        None,
        "--key", "-k",
        help="Путь к файлу с ключом (для RSA - публичный ключ)"
    ),
    encoding: Encoding = typer.Option(
        Encoding.base64,
        "--encoding", "-e",
        help="Кодировка результата"
    ),
):
    """
    Шифрование данных различными алгоритмами

    Примеры:

      # Кузнечик (симметричное шифрование)
      infbez crypto encrypt "Секретное сообщение" -a kuznechik

      # RSA (асимметричное шифрование)
      infbez crypto encrypt document.txt -a rsa -f --key public.json -o encrypted.bin
    """
    try:
        # Чтение входных данных
        data = read_file_or_text(input_data, is_file)

        if algorithm == Algorithm.kuznechik:
            # Ленивый импорт
            from algorithms.kuznechik.kuznechik import Kuznechik

            # Валидация размера (max 1MB для Кузнечик)
            validate_data_size(data, 1024 * 1024, "Кузнечик")

            # Генерация ключа и создание шифра
            key = os.urandom(32)  # 256-bit key
            cipher = Kuznechik(key)

            # PKCS#7 padding
            block_size = 16
            padding_length = block_size - (len(data) % block_size)
            padded_data = data + bytes([padding_length] * padding_length)

            # Шифрование блоками
            encrypted_blocks = []
            for i in range(0, len(padded_data), block_size):
                block = padded_data[i:i + block_size]
                encrypted_block = cipher.encrypt(block)
                encrypted_blocks.append(encrypted_block)

            encrypted_data = b''.join(encrypted_blocks)

            # Формирование результата
            result = {
                "encrypted": encode_data(encrypted_data, encoding.value),
                "key": encode_data(key, encoding.value),
                "algorithm": "kuznechik",
                "encoding": encoding.value,
                "original_size": len(data),
                "encrypted_size": len(encrypted_data),
                "timestamp": get_timestamp()
            }

            write_output(result, output, as_json=True)
            print_success(f"Данные зашифрованы ({format_bytes(len(data))} → {format_bytes(len(encrypted_data))})")

        elif algorithm == Algorithm.rsa:
            # Ленивый импорт
            from algorithms.rsa_32768 import RSA32768

            # RSA шифрование
            if not key_file:
                print_error("Для RSA требуется публичный ключ (--key)")
                raise typer.Exit(code=3)

            # Валидация размера (max 4090 байт для RSA-32768)
            validate_data_size(data, 4090, "RSA-32768")

            # Загрузка ключа
            key_data = load_json_file(key_file)

            # Создание RSA объекта
            rsa = RSA32768(
                public_key={
                    'n': int(key_data['public_key']['n'], 16),
                    'e': key_data['public_key']['e']
                }
            )

            # Шифрование
            encrypted = rsa.encrypt(data)

            # Формирование результата
            result = {
                "encrypted": encode_data(encrypted, encoding.value),
                "algorithm": "rsa-32768",
                "encoding": encoding.value,
                "key_fingerprint": key_data.get('key_id', 'unknown')[:16],
                "original_size": len(data),
                "encrypted_size": len(encrypted),
                "timestamp": get_timestamp()
            }

            write_output(result, output, as_json=True)
            print_success(f"Данные зашифрованы RSA-32768 ({format_bytes(len(data))})")

    except FileNotFoundError as e:
        print_error(f"Файл не найден: {e}")
        raise typer.Exit(code=1)
    except ValueError as e:
        print_error(f"Ошибка валидации: {e}")
        raise typer.Exit(code=2)
    except Exception as e:
        print_error(f"Ошибка шифрования: {e}")
        raise typer.Exit(code=4)


@app.command("decrypt")
def decrypt(
    input_data: str = typer.Argument(..., help="Зашифрованные данные или путь к файлу"),
    algorithm: Algorithm = typer.Option(
        Algorithm.kuznechik,
        "--algorithm", "-a",
        help="Алгоритм расшифрования"
    ),
    key_file: Path = typer.Option(
        ...,
        "--key", "-k",
        help="Путь к файлу с ключом (обязательно)"
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output", "-o",
        help="Путь для сохранения результата"
    ),
    is_file: bool = typer.Option(
        False,
        "--file", "-f",
        help="INPUT - путь к файлу"
    ),
    encoding: Encoding = typer.Option(
        Encoding.base64,
        "--encoding", "-e",
        help="Кодировка входных данных"
    ),
):
    """
    Расшифрование данных

    Примеры:

      # Кузнечик
      infbez crypto decrypt "8f3a9b2c..." -a kuznechik -k key.json

      # RSA
      infbez crypto decrypt encrypted.bin -a rsa -k private.json -f -o decrypted.txt
    """
    try:
        # Загрузка зашифрованных данных
        if is_file:
            encrypted_data_obj = load_json_file(Path(input_data))
            encrypted_bytes = decode_data(encrypted_data_obj['encrypted'], encrypted_data_obj.get('encoding', 'base64'))
        else:
            encrypted_bytes = decode_data(input_data, encoding.value)

        if algorithm == Algorithm.kuznechik:
            # Ленивый импорт
            from algorithms.kuznechik.kuznechik import Kuznechik

            # Загрузка ключа
            if is_file:
                key = decode_data(encrypted_data_obj['key'], encrypted_data_obj.get('encoding', 'base64'))
            else:
                key_data = load_json_file(key_file)
                key = decode_data(key_data['key'], key_data.get('encoding', 'base64'))

            # Расшифрование с ключом
            cipher = Kuznechik(key)
            block_size = 16

            decrypted_blocks = []
            for i in range(0, len(encrypted_bytes), block_size):
                block = encrypted_bytes[i:i + block_size]
                decrypted_block = cipher.decrypt(block)
                decrypted_blocks.append(decrypted_block)

            decrypted_data = b''.join(decrypted_blocks)

            # Удаление PKCS#7 padding
            padding_length = decrypted_data[-1]
            decrypted_data = decrypted_data[:-padding_length]

            # Вывод результата
            if output:
                with open(output, 'wb') as f:
                    f.write(decrypted_data)
                print_success(f"Данные расшифрованы и сохранены в {output}")
            else:
                try:
                    console.print(decrypted_data.decode('utf-8'))
                except UnicodeDecodeError:
                    console.print(f"[yellow]Бинарные данные ({len(decrypted_data)} байт)[/yellow]")
                    console.print(f"Используйте --output для сохранения в файл")

        elif algorithm == Algorithm.rsa:
            # Ленивый импорт
            from algorithms.rsa_32768 import RSA32768

            # Загрузка приватного ключа
            key_data = load_json_file(key_file)

            rsa = RSA32768(
                public_key={
                    'n': int(key_data['public_key']['n'], 16),
                    'e': key_data['public_key']['e']
                },
                private_key={
                    'd': int(key_data['private_key']['d'], 16),
                    'p': int(key_data['private_key']['p'], 16),
                    'q': int(key_data['private_key']['q'], 16)
                }
            )

            # Расшифрование
            decrypted_data = rsa.decrypt(encrypted_bytes)

            # Вывод результата
            if output:
                with open(output, 'wb') as f:
                    f.write(decrypted_data)
                print_success(f"Данные расшифрованы RSA-32768 и сохранены в {output}")
            else:
                try:
                    console.print(decrypted_data.decode('utf-8'))
                except UnicodeDecodeError:
                    console.print(f"[yellow]Бинарные данные ({len(decrypted_data)} байт)[/yellow]")

    except FileNotFoundError as e:
        print_error(f"Файл не найден: {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        print_error(f"Ошибка расшифрования: {e}")
        raise typer.Exit(code=4)


@app.command("hash")
def hash_data(
    input_data: str = typer.Argument(..., help="Текст или путь к файлу"),
    is_file: bool = typer.Option(
        False,
        "--file", "-f",
        help="INPUT - путь к файлу"
    ),
    encoding: Encoding = typer.Option(
        Encoding.hex,
        "--encoding", "-e",
        help="Формат вывода"
    ),
    verify: Optional[str] = typer.Option(
        None,
        "--verify", "-v",
        help="Проверить хеш (сравнить с этим значением)"
    ),
):
    """
    Хеширование данных с использованием Стрибог-512

    Примеры:

      # Хеширование строки
      infbez crypto hash "Hello, World!"

      # Хеширование файла
      infbez crypto hash document.pdf -f

      # Проверка хеша
      infbez crypto hash document.pdf -f --verify "9a8b7c6d..."
    """
    try:
        # Ленивый импорт
        from algorithms.streebog.streebog import streebog_512

        # Чтение данных
        data = read_file_or_text(input_data, is_file)

        # Хеширование
        hash_bytes = streebog_512(data)
        hash_str = encode_data(hash_bytes, encoding.value)

        # Проверка хеша (если указан)
        if verify:
            if hash_str.lower() == verify.lower():
                print_success("Хеш совпадает")
                console.print(f"[green]{hash_str}[/green]")
            else:
                print_error("Хеш НЕ совпадает")
                console.print(f"  Ожидалось: [dim]{verify}[/dim]")
                console.print(f"  Получено:  [red]{hash_str}[/red]")
                raise typer.Exit(code=1)
        else:
            # Вывод хеша
            if is_file:
                result = {
                    "hash": hash_str,
                    "algorithm": "streebog-512",
                    "file": input_data,
                    "size": len(data),
                    "encoding": encoding.value
                }
                write_output(result, None, as_json=True)
            else:
                console.print(hash_str)

    except FileNotFoundError as e:
        print_error(f"Файл не найден: {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        print_error(f"Ошибка хеширования: {e}")
        raise typer.Exit(code=4)


if __name__ == "__main__":
    app()
