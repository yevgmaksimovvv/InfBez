"""
Команды для тестирования и бенчмарков
"""

import typer
from pathlib import Path
from typing import Optional, List
import sys
import time
import os
import statistics

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cli.utils import (
    console, print_success, print_error, print_warning, print_info,
    load_json_file, save_json_file, create_table, format_time,
    create_progress, get_timestamp
)

app = typer.Typer(help="Тестирование и бенчмарки")

# Проверка доступности RSA
RSA_AVAILABLE = False
try:
    from algorithms.rsa_32768 import RSA32768
    RSA_AVAILABLE = True
except ImportError:
    RSA_AVAILABLE = False


@app.command("all")
def test_all(
    iterations: int = typer.Option(
        10,
        "--iterations", "-i",
        min=1, max=100,
        help="Количество итераций для Стрибог и Кузнечик"
    ),
    data_sizes: Optional[List[int]] = typer.Option(
        None,
        "--data-sizes", "-s",
        help="Размеры тестовых данных в байтах"
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output", "-o",
        help="Сохранить результаты в JSON"
    ),
    show_progress: bool = typer.Option(
        True,
        "--progress/--no-progress", "-p",
        help="Показывать прогресс-бар"
    ),
    skip_rsa: bool = typer.Option(
        False,
        "--skip-rsa",
        help="Пропустить RSA тестирование"
    ),
    rsa_keys: Optional[Path] = typer.Option(
        None,
        "--rsa-keys",
        help="Путь к RSA ключам (если не указан, RSA будет пропущен)"
    ),
):
    """
    Комплексное тестирование всех алгоритмов по очереди

    Примеры:

      # Все алгоритмы (без RSA)
      infbez test all --progress

      # Все алгоритмы включая RSA
      infbez test all --rsa-keys keys.json

      # Пропустить RSA
      infbez test all --skip-rsa

      # Кастомные размеры данных
      infbez test all -s 1024 -s 4096 -s 8192
    """
    try:
        # Размеры данных
        if not data_sizes:
            test_sizes = [16, 64, 256, 1024, 4096]
        else:
            test_sizes = data_sizes

        console.print("\n[bold cyan]═══════════════════════════════════════════════════════════[/bold cyan]")
        console.print("[bold cyan]  КОМПЛЕКСНОЕ ТЕСТИРОВАНИЕ ВСЕХ АЛГОРИТМОВ[/bold cyan]")
        console.print("[bold cyan]═══════════════════════════════════════════════════════════[/bold cyan]\n")

        print_info(f"Итерации: {iterations}")
        print_info(f"Размеры данных: {test_sizes} байт\n")

        results = {
            "timestamp": get_timestamp(),
            "iterations": iterations,
            "data_sizes": test_sizes,
            "results": {}
        }

        # 1. Тестирование Стрибог
        console.print("\n[bold yellow]1/3 Стрибог-512 (ГОСТ 34.11-2018)[/bold yellow]")
        algo_results = benchmark_streebog(test_sizes, iterations, show_progress)
        results['results']['streebog'] = algo_results

        # 2. Тестирование Кузнечик
        console.print("\n[bold yellow]2/3 Кузнечик (ГОСТ Р 34.12-2018)[/bold yellow]")
        algo_results = benchmark_kuznechik(test_sizes, iterations, show_progress)
        results['results']['kuznechik'] = algo_results

        # 3. Тестирование RSA
        if not skip_rsa:
            console.print("\n[bold yellow]3/3 RSA-32768[/bold yellow]")
            if not RSA_AVAILABLE:
                print_warning("RSA-32768 пропущен: gmpy2 не установлен")
                print_info("Установите: pip install gmpy2")
            elif rsa_keys is None:
                print_warning("RSA-32768 пропущен: не указаны ключи")
                print_info("Используйте: infbez test all --rsa-keys <file>")
                print_info("Или пропустите RSA: infbez test all --skip-rsa")
            else:
                try:
                    rsa_iterations = min(iterations, 5)  # Ограничение для RSA
                    algo_results = benchmark_rsa(rsa_keys, test_sizes, rsa_iterations, show_progress)
                    results['results']['rsa'] = algo_results
                except Exception as e:
                    print_error(f"Ошибка тестирования RSA: {e}")
        else:
            console.print("\n[bold yellow]3/3 RSA-32768[/bold yellow]")
            print_warning("RSA-32768 пропущен по запросу (--skip-rsa)")

        # Вывод итоговой таблицы
        display_all_results(results)

        # Сохранение результатов
        if output:
            save_json_file(results, output)
            print_success(f"\nРезультаты сохранены в {output}")

    except KeyboardInterrupt:
        print_error("\nТестирование прервано")
        raise typer.Exit(code=10)
    except Exception as e:
        print_error(f"Ошибка тестирования: {e}")
        import traceback
        traceback.print_exc()
        raise typer.Exit(code=4)


def benchmark_streebog(sizes: List[int], iterations: int, show_progress: bool) -> dict:
    """Бенчмарк Стрибог-512"""
    from algorithms.streebog.streebog import streebog_512

    console.print("[yellow]Тестирование Стрибог-512...[/yellow]")
    results = {}

    total_tests = len(sizes) * iterations

    if show_progress:
        progress = create_progress()
        task = progress.add_task("[cyan]Стрибог", total=total_tests)
        progress.start()
    else:
        progress = None

    for size in sizes:
        data = os.urandom(size)
        times = []

        for _ in range(iterations):
            start = time.perf_counter()
            streebog_512(data)
            elapsed = time.perf_counter() - start
            times.append(elapsed * 1000)  # в миллисекундах

            if progress:
                progress.update(task, advance=1)

        results[str(size)] = {
            "avg_ms": round(statistics.mean(times), 3),
            "min_ms": round(min(times), 3),
            "max_ms": round(max(times), 3),
            "std_dev": round(statistics.stdev(times) if len(times) > 1 else 0, 3)
        }

    if progress:
        progress.stop()

    return results


def benchmark_kuznechik(sizes: List[int], iterations: int, show_progress: bool) -> dict:
    """Бенчмарк Кузнечик"""
    from algorithms.kuznechik.kuznechik import Kuznechik

    console.print("[yellow]Тестирование Кузнечик...[/yellow]")
    results = {}

    total_tests = len(sizes) * iterations

    if show_progress:
        progress = create_progress()
        task = progress.add_task("[cyan]Кузнечик", total=total_tests)
        progress.start()
    else:
        progress = None

    for size in sizes:
        # Выравнивание до 16 байт
        adjusted_size = ((size + 15) // 16) * 16
        data = os.urandom(adjusted_size)
        times = []

        for _ in range(iterations):
            # Создание нового шифра для каждой итерации
            cipher = Kuznechik()

            start = time.perf_counter()
            # Шифрование блоками
            for i in range(0, len(data), 16):
                block = data[i:i + 16]
                cipher.encrypt(block)
            elapsed = time.perf_counter() - start
            times.append(elapsed * 1000)

            if progress:
                progress.update(task, advance=1)

        results[str(size)] = {
            "avg_ms": round(statistics.mean(times), 3),
            "min_ms": round(min(times), 3),
            "max_ms": round(max(times), 3),
            "std_dev": round(statistics.stdev(times) if len(times) > 1 else 0, 3)
        }

    if progress:
        progress.stop()

    return results


def benchmark_rsa(keys_path: Path, sizes: List[int], iterations: int, show_progress: bool) -> dict:
    """Бенчмарк RSA-32768"""
    if not RSA_AVAILABLE:
        raise Exception("RSA-32768 недоступен: gmpy2 не установлен")

    print_info(f"Загрузка ключей из {keys_path}")
    key_data = load_json_file(keys_path)

    # Проверка на демо режим
    if key_data.get('metadata', {}).get('demo_mode'):
        raise Exception("Ключи созданы в демо режиме и не могут использоваться для шифрования")

    # Создание RSA объекта
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

    results = {}
    max_size = 4094  # Максимальный размер для RSA-32768

    for size in sizes:
        if size > max_size:
            print_warning(f"Размер {size} байт превышает максимум {max_size} - пропущен")
            continue

        data = os.urandom(size)
        encrypt_times = []
        decrypt_times = []

        if show_progress:
            progress = create_progress()
            task = progress.add_task(f"[cyan]RSA {size}б", total=iterations)
            progress.start()

        for _ in range(iterations):
            # Шифрование
            start = time.perf_counter()
            encrypted = rsa.encrypt(data)
            encrypt_time = time.perf_counter() - start
            encrypt_times.append(encrypt_time * 1000)

            # Расшифрование
            start = time.perf_counter()
            decrypted = rsa.decrypt(encrypted)
            decrypt_time = time.perf_counter() - start
            decrypt_times.append(decrypt_time * 1000)

            # Проверка
            if decrypted != data:
                raise Exception(f"Ошибка: данные не совпадают для размера {size}")

            if show_progress:
                progress.update(task, advance=1)

        if show_progress:
            progress.stop()

        results[str(size)] = {
            "encrypt_avg_ms": round(statistics.mean(encrypt_times), 3),
            "encrypt_min_ms": round(min(encrypt_times), 3),
            "encrypt_max_ms": round(max(encrypt_times), 3),
            "decrypt_avg_ms": round(statistics.mean(decrypt_times), 3),
            "decrypt_min_ms": round(min(decrypt_times), 3),
            "decrypt_max_ms": round(max(decrypt_times), 3),
        }

    return results


def display_all_results(results: dict):
    """Отображение результатов всех алгоритмов"""
    console.print("\n[bold green]═══════════════════════════════════════════════════════════[/bold green]")
    console.print("[bold green]  ИТОГОВЫЕ РЕЗУЛЬТАТЫ[/bold green]")
    console.print("[bold green]═══════════════════════════════════════════════════════════[/bold green]\n")

    # Стрибог
    if 'streebog' in results['results']:
        console.print("[bold cyan]Стрибог-512 (Хеширование)[/bold cyan]")
        table = create_table(
            "",
            ["Размер", "Среднее", "Мин", "Макс", "Ст. откл."]
        )
        for size, metrics in results['results']['streebog'].items():
            table.add_row(
                f"{size} байт",
                f"{metrics['avg_ms']:.3f} ms",
                f"{metrics['min_ms']:.3f} ms",
                f"{metrics['max_ms']:.3f} ms",
                f"{metrics['std_dev']:.3f} ms"
            )
        console.print(table)
        console.print()

    # Кузнечик
    if 'kuznechik' in results['results']:
        console.print("[bold cyan]Кузнечик (Шифрование блоками 16 байт)[/bold cyan]")
        table = create_table(
            "",
            ["Размер", "Среднее", "Мин", "Макс", "Ст. откл."]
        )
        for size, metrics in results['results']['kuznechik'].items():
            table.add_row(
                f"{size} байт",
                f"{metrics['avg_ms']:.3f} ms",
                f"{metrics['min_ms']:.3f} ms",
                f"{metrics['max_ms']:.3f} ms",
                f"{metrics['std_dev']:.3f} ms"
            )
        console.print(table)
        console.print()

    # RSA
    if 'rsa' in results['results']:
        console.print("[bold cyan]RSA-32768 (Асимметричное шифрование)[/bold cyan]")
        table = create_table(
            "",
            ["Размер", "Операция", "Среднее", "Мин", "Макс"]
        )
        for size, metrics in results['results']['rsa'].items():
            table.add_row(
                f"{size} байт",
                "Шифрование",
                f"{metrics['encrypt_avg_ms']:.2f} ms",
                f"{metrics['encrypt_min_ms']:.2f} ms",
                f"{metrics['encrypt_max_ms']:.2f} ms"
            )
            table.add_row(
                "",
                "Расшифрование",
                f"{metrics['decrypt_avg_ms']:.2f} ms",
                f"{metrics['decrypt_min_ms']:.2f} ms",
                f"{metrics['decrypt_max_ms']:.2f} ms"
            )
        console.print(table)
        console.print()

    print_success("✓ Все тесты завершены успешно!")




if __name__ == "__main__":
    app()
