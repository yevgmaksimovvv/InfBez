"""
Команды для управления RSA ключами
"""

import typer
from pathlib import Path
from typing import Optional
import sys
import uuid
from datetime import datetime
import glob

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Ленивый импорт
# from algorithms.rsa_32768 import RSA32768, PrimeGenerator
from cli.utils import (
    console, print_success, print_error, print_warning, print_info,
    load_json_file, save_json_file, create_table, format_time,
    create_progress
)

app = typer.Typer(help="Управление RSA ключами")


@app.command("generate")
def generate(
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
        help="Имя для идентификации ключа"
    ),
    no_parallel: bool = typer.Option(
        False,
        "--no-parallel",
        help="Отключить параллельную генерацию"
    ),
):
    """
    Генерация RSA-32768 ключей

    ВАЖНО: Генерация занимает 9-28 дней на современном CPU!

    Примеры:

      infbez keys generate -o my_keys.json --name "Production Key"
      infbez keys generate --rounds 10 --no-parallel
    """
    try:
        print_warning(f"ВНИМАНИЕ: Генерация RSA-32768 ключей займет 9-28 дней!")
        print_info(f"Раунды Miller-Rabin: {rounds}")
        print_info(f"Параллелизация: {'отключена' if no_parallel else 'включена'}")

        # Спросить подтверждение
        if not typer.confirm("Продолжить генерацию ключей?"):
            print_info("Генерация отменена")
            raise typer.Exit()

        console.print("\n[bold]Начинаем генерацию ключей...[/bold]\n")

        # Ленивый импорт
        # from algorithms.rsa_32768 import PrimeGenerator

        # Создание генератора
        bits = 16384  # 16384 * 2 = 32768 бит
        # generator = PrimeGenerator(bits, rounds)

        # Генерация ключей с прогресс-баром
        with console.status("[bold green]Генерация RSA-32768 ключей...", spinner="dots") as status:
            import time
            start_time = time.time()

            # Для демонстрации - показываем прогресс
            # В реальности генерация займет дни
            console.print("[yellow]Генерация простого числа p...[/yellow]")
            # В production здесь будет вызов генератора с реальной генерацией
            # p = generator.generate_prime()

            console.print("[yellow]Генерация простого числа q...[/yellow]")
            # q = generator.generate_prime()

            # ПРИМЕЧАНИЕ: Здесь должна быть полная реализация генерации
            # Для демо используем заглушку
            print_warning("ДЕМО РЕЖИМ: Полная генерация не выполнена")
            print_info("Для реальной генерации используйте: python test_rsa.py --generate")

            elapsed = time.time() - start_time

        # Создание метаданных ключа
        key_id = str(uuid.uuid4())
        key_data = {
            "key_id": key_id,
            "name": name or f"RSA Key {datetime.now().strftime('%Y-%m-%d')}",
            "algorithm": "RSA-32768",
            "created_at": datetime.utcnow().isoformat() + 'Z',
            "miller_rabin_rounds": rounds,
            "public_key": {
                "n": "демо_значение_используйте_test_rsa.py",
                "e": 65537
            },
            "private_key": {
                "d": "демо_значение",
                "p": "демо_значение",
                "q": "демо_значение"
            },
            "metadata": {
                "bits": 32768,
                "generation_time_seconds": elapsed,
                "generation_time_human": format_time(elapsed),
                "demo_mode": True
            }
        }

        # Сохранение
        save_json_file(key_data, output)
        print_success(f"Метаданные ключа сохранены в {output}")
        print_warning("Для генерации реальных ключей используйте: python test_rsa.py --generate")

    except KeyboardInterrupt:
        print_error("\nГенерация прервана пользователем")
        raise typer.Exit(code=10)
    except Exception as e:
        print_error(f"Ошибка генерации: {e}")
        raise typer.Exit(code=4)


@app.command("list")
def list_keys(
    directory: Path = typer.Option(
        Path("./keys"),
        "--directory", "-d",
        help="Директория с ключами"
    ),
    format_type: str = typer.Option(
        "table",
        "--format", "-f",
        help="Формат вывода: table, json"
    ),
):
    """
    Список всех ключей из файлов

    Примеры:

      infbez keys list -d ./keys
      infbez keys list --format json
    """
    try:
        # Поиск JSON файлов с ключами
        if directory.exists():
            key_files = list(directory.glob("*.json"))
        else:
            key_files = list(Path(".").glob("*keys*.json"))

        if not key_files:
            print_warning(f"Ключи не найдены в {directory}")
            return

        # Загрузка информации о ключах
        keys_info = []
        for key_file in key_files:
            try:
                key_data = load_json_file(key_file)
                if 'public_key' in key_data:  # Проверка что это файл ключа
                    keys_info.append({
                        'file': key_file.name,
                        'key_id': key_data.get('key_id', 'N/A')[:16] + '...',
                        'algorithm': key_data.get('algorithm', 'N/A'),
                        'name': key_data.get('name', 'N/A'),
                        'created': key_data.get('created_at', 'N/A')[:19]
                    })
            except Exception:
                continue

        if not keys_info:
            print_warning("Валидные ключи не найдены")
            return

        # Вывод результата
        if format_type == "json":
            import json
            console.print_json(json.dumps(keys_info, indent=2))
        else:
            # Таблица
            table = create_table("RSA Ключи", ["Файл", "Key ID", "Алгоритм", "Имя", "Создан"])
            for key in keys_info:
                table.add_row(
                    key['file'],
                    key['key_id'],
                    key['algorithm'],
                    key['name'],
                    key['created']
                )
            console.print(table)

    except Exception as e:
        print_error(f"Ошибка: {e}")
        raise typer.Exit(code=1)


@app.command("export")
def export_key(
    key_file: Path = typer.Argument(..., help="Путь к файлу с ключами"),
    output: Optional[Path] = typer.Option(
        None,
        "--output", "-o",
        help="Путь для сохранения (по умолчанию: stdout)"
    ),
    format_type: str = typer.Option(
        "json",
        "--format", "-f",
        help="Формат: json, pem (только публичный ключ)"
    ),
    public_only: bool = typer.Option(
        True,
        "--public-only",
        help="Экспортировать только публичный ключ"
    ),
):
    """
    Экспорт публичного ключа

    Примеры:

      infbez keys export my_keys.json -f json -o public.json
      infbez keys export my_keys.json --no-public-only
    """
    try:
        # Загрузка ключа
        key_data = load_json_file(key_file)

        # Формирование экспорта
        if public_only:
            export_data = {
                "key_id": key_data.get('key_id'),
                "name": key_data.get('name'),
                "algorithm": key_data.get('algorithm'),
                "public_key": key_data.get('public_key')
            }
        else:
            export_data = key_data

        # Вывод
        if output:
            save_json_file(export_data, output)
            print_success(f"Ключ экспортирован в {output}")
        else:
            import json
            console.print_json(json.dumps(export_data, indent=2))

    except Exception as e:
        print_error(f"Ошибка экспорта: {e}")
        raise typer.Exit(code=1)


@app.command("import")
def import_key(
    input_file: Path = typer.Argument(..., help="Путь к файлу с ключом"),
    output: Path = typer.Option(
        Path("imported_key.json"),
        "--output", "-o",
        help="Путь для сохранения"
    ),
):
    """
    Импорт ключа из файла

    Примеры:

      infbez keys import external_key.json -o my_key.json
    """
    try:
        # Загрузка
        key_data = load_json_file(input_file)

        # Валидация
        if 'public_key' not in key_data:
            print_error("Файл не содержит валидного ключа")
            raise typer.Exit(code=2)

        # Добавление метаданных если отсутствуют
        if 'key_id' not in key_data:
            key_data['key_id'] = str(uuid.uuid4())
        if 'created_at' not in key_data:
            key_data['created_at'] = datetime.utcnow().isoformat() + 'Z'

        # Сохранение
        save_json_file(key_data, output)
        print_success(f"Ключ импортирован в {output}")
        print_info(f"Key ID: {key_data['key_id']}")

    except Exception as e:
        print_error(f"Ошибка импорта: {e}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
