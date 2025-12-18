"""
Команды для RSA-32768 шифрования и управления ключами
"""

import sys
import typer
from pathlib import Path
from typing import Optional
import uuid
from datetime import datetime

# Увеличение лимита конвертации int для RSA-32768
sys.set_int_max_str_digits(20000)

from cli.utils import (
    console, print_success, print_error, print_warning, print_info,
    encode_data, decode_data, load_json_file, save_json_file,
    read_input_data, get_timestamp, format_bytes, create_table
)
from cli.services.crypto_service import RSAService
from cli.exit_codes import ExitCode

app = typer.Typer(help="RSA-32768 шифрование и управление ключами")

# Проверка доступности RSA
RSA_AVAILABLE = False
try:
    from algorithms.rsa_32768 import RSA32768
    RSA_AVAILABLE = True
except ImportError:
    pass


@app.command("encrypt")
def encrypt(
    input_data: str = typer.Argument(..., help="Текст или путь к файлу"),
    key: Path = typer.Option(..., "--key", "-k", help="Путь к публичному ключу"),
    output: Optional[Path] = typer.Option(
        None,
        "--output", "-o",
        help="Путь для сохранения (по умолчанию: encrypted.json)"
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
    force: bool = typer.Option(
        False,
        "--force", "-f",
        help="Перезаписать файл если существует"
    ),
):
    """
    Шифрование данных RSA-32768

    Примеры:

      rsa encrypt "Секретное сообщение" --key public.json
      rsa encrypt document.txt -k public.json -o encrypted.json
    """
    if not RSA_AVAILABLE:
        print_error("RSA-32768 недоступен: установите gmpy2")
        print_info("Установка: pip install gmpy2")
        raise typer.Exit(code=ExitCode.GMPY2_NOT_AVAILABLE)

    try:
        # Чтение с учетом флагов
        data = read_input_data(input_data, force_file=force_file, force_text=force_text)

        # Валидация размера
        if len(data) > RSAService.MAX_DATA_SIZE:
            print_error(f"Файл слишком большой: {format_bytes(len(data))} (макс. {format_bytes(RSAService.MAX_DATA_SIZE)})")
            raise typer.Exit(code=ExitCode.DATA_TOO_LARGE)

        # Загрузка публичного ключа
        key_data = load_json_file(key)
        n_str = key_data['public_key']['n']
        # Поддержка hex и decimal форматов
        if isinstance(n_str, str) and n_str.startswith(('0x', '0X')):
            n_value = int(n_str, 16)
        elif isinstance(n_str, str):
            n_value = int(n_str)
        else:
            n_value = n_str

        public_key = {
            'n': n_value,
            'e': key_data['public_key']['e']
        }

        # Шифрование
        encrypted_data = RSAService.encrypt(data, public_key)

        # Формирование результата
        result = {
            "encrypted": encode_data(encrypted_data, 'base64'),
            "algorithm": "rsa-32768",
            "encoding": "base64",
            "key_fingerprint": key_data.get('key_id', 'unknown')[:16],
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
        print_success(f"Зашифровано RSA-32768: {format_bytes(len(data))}")
        console.print(f"Сохранено в [cyan]{output}[/cyan]")

    except FileNotFoundError as e:
        print_error(f"Файл не найден: {e}")
        raise typer.Exit(code=ExitCode.FILE_NOT_FOUND)
    except (KeyError, ValueError) as e:
        print_error(f"Ошибка ключа: {e}")
        raise typer.Exit(code=ExitCode.INVALID_KEY)
    except Exception as e:
        print_error(f"Ошибка шифрования: {e}")
        raise typer.Exit(code=ExitCode.ENCRYPTION_ERROR)


@app.command("decrypt")
def decrypt(
    input_file: Path = typer.Argument(..., help="Файл с зашифрованными данными"),
    key: Path = typer.Option(..., "--key", "-k", help="Путь к приватному ключу"),
    output: Optional[Path] = typer.Option(
        None,
        "--output", "-o",
        help="Путь для сохранения результата"
    ),
    force: bool = typer.Option(
        False,
        "--force", "-f",
        help="Перезаписать файл если существует"
    ),
):
    """
    Расшифрование данных RSA-32768

    Примеры:

      rsa decrypt encrypted.json --key private.json
      rsa decrypt encrypted.json -k private.json -o decrypted.txt
    """
    if not RSA_AVAILABLE:
        print_error("RSA-32768 недоступен: установите gmpy2")
        print_info("Установка: pip install gmpy2")
        raise typer.Exit(code=ExitCode.GMPY2_NOT_AVAILABLE)

    try:
        # Загрузка зашифрованных данных
        encrypted_obj = load_json_file(input_file)
        encrypted_data = decode_data(
            encrypted_obj['encrypted'],
            encrypted_obj.get('encoding', 'base64')
        )

        # Загрузка ключей
        key_data = load_json_file(key)

        # Поддержка hex и decimal форматов
        def parse_key_value(val):
            if isinstance(val, str) and val.startswith(('0x', '0X')):
                return int(val, 16)
            elif isinstance(val, str):
                return int(val)
            return val

        public_key = {
            'n': parse_key_value(key_data['public_key']['n']),
            'e': key_data['public_key']['e']
        }
        private_key = {
            'd': parse_key_value(key_data['private_key']['d']),
            'p': parse_key_value(key_data['private_key']['p']),
            'q': parse_key_value(key_data['private_key']['q'])
        }

        # Расшифрование
        decrypted_data = RSAService.decrypt(encrypted_data, public_key, private_key)

        # Вывод результата
        if output:
            # Проверка перезаписи
            if output.exists() and not force:
                print_error(f"Файл {output} уже существует. Используйте --force для перезаписи")
                raise typer.Exit(code=ExitCode.FILE_WRITE_ERROR)

            with open(output, 'wb') as f:
                f.write(decrypted_data)
            print_success(f"Расшифровано RSA-32768: {format_bytes(len(decrypted_data))}")
            console.print(f"Сохранено в [cyan]{output}[/cyan]")
        else:
            try:
                console.print(decrypted_data.decode('utf-8'))
            except UnicodeDecodeError:
                print_error("Бинарные данные - используйте --output для сохранения")
                raise typer.Exit(code=ExitCode.INVALID_FORMAT)

    except FileNotFoundError as e:
        print_error(f"Файл не найден: {e}")
        raise typer.Exit(code=ExitCode.FILE_NOT_FOUND)
    except KeyError as e:
        print_error(f"Некорректный формат: {e}")
        raise typer.Exit(code=ExitCode.INVALID_FORMAT)
    except Exception as e:
        print_error(f"Ошибка расшифрования: {e}")
        raise typer.Exit(code=ExitCode.DECRYPTION_ERROR)


@app.command("keygen")
def keygen(
    output: Path = typer.Option(
        "rsa_keys.json",
        "--output", "-o",
        help="Путь для сохранения ключей"
    ),
    rounds: int = typer.Option(
        15,
        "--rounds", "-r",
        min=10, max=20,
        help="Количество раундов Miller-Rabin (10-20)"
    ),
    name: Optional[str] = typer.Option(
        None,
        "--name", "-n",
        help="Имя ключа"
    ),
    parallel: bool = typer.Option(
        True,
        "--parallel/--no-parallel",
        help="Параллельная генерация p и q"
    ),
    force: bool = typer.Option(
        False,
        "--force", "-f",
        help="Перезаписать файл если существует"
    ),
):
    """
    Генерация RSA-32768 ключей

    ⚠️  ВАЖНО: Генерация занимает 5-20 дней на современном CPU!

    Примеры:

      rsa keygen -o my_keys.json --name "Production Key"
      rsa keygen --rounds 10 --no-parallel
    """
    if not RSA_AVAILABLE:
        print_error("RSA-32768 недоступен: установите gmpy2")
        print_info("Установка: pip install gmpy2")
        raise typer.Exit(code=ExitCode.GMPY2_NOT_AVAILABLE)

    try:
        print_warning("⚠️  Генерация RSA-32768 ключей займет 5-20 дней!")
        print_info(f"Раунды Miller-Rabin: {rounds}")
        print_info(f"Параллелизация: {'включена' if parallel else 'отключена'}")
        console.print()

        if not typer.confirm("Продолжить генерацию ключей?"):
            print_info("Генерация отменена")
            raise typer.Exit()

        console.print("\n[bold green]Начинаем генерацию RSA-32768 ключей...[/bold green]\n")

        # Импорт функций генерации
        from algorithms.rsa_32768 import generate_prime_pair_parallel, RSA32768
        import time

        start_time = time.time()

        # Генерация пары простых чисел
        console.print("[yellow]Генерация простых чисел p и q...[/yellow]")
        console.print("[dim]Это займет несколько дней. Прогресс будет логироваться каждые 30 секунд.[/dim]\n")

        with console.status("[bold green]Генерация ключей...", spinner="dots"):
            p_stats, q_stats = generate_prime_pair_parallel(
                bits=16384,
                miller_rabin_rounds=rounds
            )

        p = p_stats.prime
        q = q_stats.prime

        # Создание RSA объекта и вычисление ключей
        console.print("[yellow]Вычисление ключей RSA...[/yellow]")
        rsa = RSA32768.generate(p=p, q=q, e=65537)

        elapsed = time.time() - start_time

        # Формирование результата
        key_id = str(uuid.uuid4())
        key_data = {
            "key_id": key_id,
            "name": name or f"RSA Key {datetime.now().strftime('%Y-%m-%d')}",
            "algorithm": "RSA-32768",
            "created_at": datetime.utcnow().isoformat() + 'Z',
            "miller_rabin_rounds": rounds,
            "public_key": {
                "n": hex(int(rsa.n)),
                "e": rsa.e
            },
            "private_key": {
                "d": hex(int(rsa.d)),
                "p": hex(int(rsa.p)),
                "q": hex(int(rsa.q))
            },
            "metadata": {
                "bits": 32768,
                "generation_time_seconds": elapsed,
                "generation_time_days": elapsed / 86400,
                "p_generation": {
                    "attempts": p_stats.attempts,
                    "time_seconds": p_stats.elapsed_seconds,
                },
                "q_generation": {
                    "attempts": q_stats.attempts,
                    "time_seconds": q_stats.elapsed_seconds,
                }
            }
        }

        # Сохранение
        # Проверка перезаписи
        if output.exists() and not force:
            print_error(f"Файл {output} уже существует. Используйте --force для перезаписи")
            raise typer.Exit(code=ExitCode.FILE_WRITE_ERROR)

        save_json_file(key_data, output)

        print_success(f"✓ RSA-32768 ключи успешно сгенерированы!")
        console.print(f"Сохранено в [cyan]{output}[/cyan]")
        console.print(f"Время генерации: [green]{elapsed/86400:.2f} дней[/green] ({elapsed/3600:.1f} часов)")
        console.print(f"Key ID: [dim]{key_id}[/dim]")

    except KeyboardInterrupt:
        print_error("\nГенерация прервана пользователем")
        raise typer.Exit(code=ExitCode.OPERATION_CANCELLED)
    except Exception as e:
        print_error(f"Ошибка генерации: {e}")
        import traceback
        traceback.print_exc()
        raise typer.Exit(code=ExitCode.KEY_GENERATION_ERROR)


@app.command("keys")
def list_keys(
    directory: Optional[Path] = typer.Option(
        None,
        "--directory", "-d",
        help="Директория с ключами (по умолчанию: ./keys и .)"
    ),
):
    """
    Список RSA ключей

    Примеры:

      rsa keys
      rsa keys -d ./my_keys
    """
    try:
        # Поиск ключей
        if directory and directory.exists():
            key_files = list(directory.glob("*.json"))
        else:
            # Поиск в стандартных местах
            key_files = []
            for search_dir in [Path("./keys"), Path(".")]:
                if search_dir.exists():
                    key_files.extend(search_dir.glob("*keys*.json"))
                    key_files.extend(search_dir.glob("*rsa*.json"))

        if not key_files:
            print_warning("RSA ключи не найдены")
            return

        # Загрузка информации о ключах
        keys_info = []
        for key_file in key_files:
            try:
                key_data = load_json_file(key_file)
                if 'public_key' in key_data and 'algorithm' in key_data:
                    # Проверка размера ключа для валидации
                    n_value = key_data['public_key'].get('n', '')
                    is_valid = len(n_value) > 100  # Реальный ключ имеет большую длину

                    keys_info.append({
                        'file': key_file.name,
                        'key_id': key_data.get('key_id', 'N/A')[:12] + '...',
                        'name': key_data.get('name', 'N/A'),
                        'created': key_data.get('created_at', 'N/A')[:10],
                        'status': '✓ Валидный' if is_valid else '⚠️  Тестовый'
                    })
            except Exception:
                continue

        if not keys_info:
            print_warning("Валидные RSA ключи не найдены")
            return

        # Вывод таблицы
        table = create_table("RSA-32768 Ключи", ["Файл", "Key ID", "Имя", "Создан", "Статус"])
        for key in keys_info:
            table.add_row(
                key['file'],
                key['key_id'],
                key['name'],
                key['created'],
                key['status']
            )
        console.print(table)

    except Exception as e:
        print_error(f"Ошибка: {e}")
        raise typer.Exit(code=ExitCode.UNKNOWN_ERROR)


@app.command("export")
def export_key(
    key_file: Path = typer.Argument(..., help="Путь к файлу с ключами"),
    output: Optional[Path] = typer.Option(
        None,
        "--output", "-o",
        help="Путь для сохранения"
    ),
    public: bool = typer.Option(
        True,
        "--public/--full",
        help="Экспортировать только публичный ключ"
    ),
    force: bool = typer.Option(
        False,
        "--force", "-f",
        help="Перезаписать файл если существует"
    ),
):
    """
    Экспорт RSA ключа

    Примеры:

      rsa export my_keys.json --public -o public.json
      rsa export my_keys.json --full
    """
    try:
        key_data = load_json_file(key_file)

        if public:
            export_data = {
                "key_id": key_data.get('key_id'),
                "name": key_data.get('name'),
                "algorithm": key_data.get('algorithm'),
                "public_key": key_data.get('public_key')
            }
        else:
            export_data = key_data

        if output:
            # Проверка перезаписи
            if output.exists() and not force:
                print_error(f"Файл {output} уже существует. Используйте --force для перезаписи")
                raise typer.Exit(code=ExitCode.FILE_WRITE_ERROR)

            save_json_file(export_data, output)
            print_success(f"Ключ экспортирован в {output}")
        else:
            import json
            console.print_json(json.dumps(export_data, indent=2))

    except Exception as e:
        print_error(f"Ошибка экспорта: {e}")
        raise typer.Exit(code=ExitCode.UNKNOWN_ERROR)


@app.command("import")
def import_key(
    input_file: Path = typer.Argument(..., help="Путь к файлу с ключом"),
    output: Path = typer.Option(
        Path("imported_key.json"),
        "--output", "-o",
        help="Путь для сохранения"
    ),
    force: bool = typer.Option(
        False,
        "--force", "-f",
        help="Перезаписать файл если существует"
    ),
):
    """
    Импорт RSA ключа

    Примеры:

      rsa import external_key.json
      rsa import external_key.json -o my_key.json
    """
    try:
        key_data = load_json_file(input_file)

        # Валидация
        if 'public_key' not in key_data:
            print_error("Файл не содержит валидного RSA ключа")
            raise typer.Exit(code=ExitCode.INVALID_KEY)

        # Добавление метаданных если отсутствуют
        if 'key_id' not in key_data:
            key_data['key_id'] = str(uuid.uuid4())
        if 'created_at' not in key_data:
            key_data['created_at'] = datetime.utcnow().isoformat() + 'Z'
        if 'algorithm' not in key_data:
            key_data['algorithm'] = 'RSA-32768'

        # Проверка перезаписи
        if output.exists() and not force:
            print_error(f"Файл {output} уже существует. Используйте --force для перезаписи")
            raise typer.Exit(code=ExitCode.FILE_WRITE_ERROR)

        save_json_file(key_data, output)
        print_success(f"Ключ импортирован в {output}")
        print_info(f"Key ID: {key_data['key_id']}")

    except Exception as e:
        print_error(f"Ошибка импорта: {e}")
        raise typer.Exit(code=ExitCode.UNKNOWN_ERROR)


if __name__ == "__main__":
    app()
