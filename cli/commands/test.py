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

# Ленивый импорт
# from algorithms.kuznechik.kuznechik import Kuznechik
# from algorithms.streebog.streebog import Streebog
# from algorithms.rsa_32768 import RSA32768
from cli.utils import (
    console, print_success, print_error, print_warning, print_info,
    load_json_file, save_json_file, create_table, format_time,
    create_progress, get_timestamp
)

app = typer.Typer(help="Тестирование и бенчмарки")


@app.command("benchmark")
def benchmark(
    algorithms: Optional[List[str]] = typer.Option(
        None,
        "--algorithms", "-a",
        help="Список алгоритмов: streebog, kuznechik, rsa (по умолчанию: все)"
    ),
    iterations: int = typer.Option(
        10,
        "--iterations", "-i",
        min=1, max=1000,
        help="Количество итераций"
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
):
    """
    Комплексное тестирование всех алгоритмов

    Примеры:

      # Все алгоритмы
      infbez test benchmark --progress

      # Только Стрибог
      infbez test benchmark -a streebog -i 100 -o results.json

      # Кастомные размеры данных
      infbez test benchmark -s 1024 -s 4096 -s 8192
    """
    try:
        # Определение алгоритмов для тестирования
        if not algorithms:
            test_algorithms = ['streebog', 'kuznechik']
        else:
            test_algorithms = algorithms

        # Размеры данных
        if not data_sizes:
            test_sizes = [16, 64, 256, 1024, 4096]
        else:
            test_sizes = data_sizes

        console.print("\n[bold cyan]Запуск бенчмарков...[/bold cyan]\n")
        print_info(f"Алгоритмы: {', '.join(test_algorithms)}")
        print_info(f"Итерации: {iterations}")
        print_info(f"Размеры данных: {test_sizes} байт\n")

        results = {
            "timestamp": get_timestamp(),
            "iterations": iterations,
            "data_sizes": test_sizes,
            "results": {}
        }

        # Тестирование каждого алгоритма
        for algo in test_algorithms:
            if algo == 'streebog':
                algo_results = benchmark_streebog(test_sizes, iterations, show_progress)
                results['results']['streebog'] = algo_results

            elif algo == 'kuznechik':
                algo_results = benchmark_kuznechik(test_sizes, iterations, show_progress)
                results['results']['kuznechik'] = algo_results

            elif algo == 'rsa':
                print_warning("RSA бенчмарк требует готовых ключей")
                print_info("Используйте: infbez test rsa --keys <file>")

        # Вывод итоговой таблицы
        display_benchmark_results(results)

        # Сохранение результатов
        if output:
            save_json_file(results, output)
            print_success(f"\nРезультаты сохранены в {output}")

    except KeyboardInterrupt:
        print_error("\nТестирование прервано")
        raise typer.Exit(code=10)
    except Exception as e:
        print_error(f"Ошибка тестирования: {e}")
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
    cipher = Kuznechik()
    key = os.urandom(32)
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
            start = time.perf_counter()
            # Шифрование блоками
            for i in range(0, len(data), 16):
                block = data[i:i + 16]
                cipher.encrypt(block, key)
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


def display_benchmark_results(results: dict):
    """Отображение результатов бенчмарка в виде таблицы"""
    console.print("\n[bold green]Результаты бенчмарков[/bold green]\n")

    table = create_table(
        "Производительность",
        ["Алгоритм", "Размер данных", "Среднее", "Мин", "Макс", "Ст. откл."]
    )

    for algo, algo_results in results['results'].items():
        for size, metrics in algo_results.items():
            table.add_row(
                algo.capitalize(),
                f"{size} байт",
                f"{metrics['avg_ms']:.3f} ms",
                f"{metrics['min_ms']:.3f} ms",
                f"{metrics['max_ms']:.3f} ms",
                f"{metrics['std_dev']:.3f} ms"
            )

    console.print(table)


@app.command("streebog")
def test_streebog(
    iterations: int = typer.Option(
        10,
        "--iterations", "-i",
        help="Количество итераций"
    ),
    data_sizes: Optional[List[int]] = typer.Option(
        None,
        "--data-sizes", "-s",
        help="Размеры данных"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose", "-v",
        help="Подробный вывод"
    ),
):
    """
    Специализированный тест Стрибог-512

    Примеры:

      infbez test streebog -i 50 --verbose
    """
    sizes = data_sizes or [16, 64, 256, 1024, 4096]
    results = benchmark_streebog(sizes, iterations, True)
    display_benchmark_results({
        "timestamp": get_timestamp(),
        "iterations": iterations,
        "results": {"streebog": results}
    })


@app.command("kuznechik")
def test_kuznechik(
    iterations: int = typer.Option(
        10,
        "--iterations", "-i",
        help="Количество итераций"
    ),
    data_sizes: Optional[List[int]] = typer.Option(
        None,
        "--data-sizes", "-s",
        help="Размеры данных"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose", "-v",
        help="Подробный вывод"
    ),
):
    """
    Специализированный тест Кузнечик

    Примеры:

      infbez test kuznechik -i 50 -s 1024 -s 4096
    """
    sizes = data_sizes or [16, 64, 256, 1024, 4096]
    results = benchmark_kuznechik(sizes, iterations, True)
    display_benchmark_results({
        "timestamp": get_timestamp(),
        "iterations": iterations,
        "results": {"kuznechik": results}
    })


@app.command("rsa")
def test_rsa(
    keys: Path = typer.Option(
        ...,
        "--keys", "-k",
        help="Путь к файлу с RSA ключами (обязательно)"
    ),
    iterations: int = typer.Option(
        5,
        "--iterations", "-i",
        min=1, max=100,
        help="Количество итераций"
    ),
    data_size: int = typer.Option(
        1024,
        "--data-size", "-s",
        min=16, max=4090,
        help="Размер тестовых данных (16-4090 байт)"
    ),
):
    """
    Специализированный тест RSA-32768 (требуются ключи)

    Примеры:

      infbez test rsa --keys my_keys.json -i 10 -s 2048
    """
    try:
        from algorithms.rsa_32768 import RSA32768

        # Загрузка ключей
        print_info(f"Загрузка ключей из {keys}")
        key_data = load_json_file(keys)

        # Проверка на демо режим
        if key_data.get('metadata', {}).get('demo_mode'):
            print_error("Ключи созданы в демо режиме и не могут использоваться для шифрования")
            print_info("Используйте: python test_rsa.py --generate для генерации реальных ключей")
            raise typer.Exit(code=2)

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

        console.print(f"\n[yellow]Тестирование RSA-32768 ({iterations} итераций, {data_size} байт)...[/yellow]\n")

        # Генерация тестовых данных
        test_data = os.urandom(data_size)

        encrypt_times = []
        decrypt_times = []

        with create_progress() as progress:
            task = progress.add_task("[cyan]RSA тест", total=iterations)

            for i in range(iterations):
                # Шифрование
                start = time.perf_counter()
                encrypted = rsa.encrypt(test_data)
                encrypt_time = time.perf_counter() - start
                encrypt_times.append(encrypt_time * 1000)

                # Расшифрование
                start = time.perf_counter()
                decrypted = rsa.decrypt(encrypted)
                decrypt_time = time.perf_counter() - start
                decrypt_times.append(decrypt_time * 1000)

                # Проверка корректности
                if decrypted != test_data:
                    print_error(f"Ошибка в итерации {i + 1}: данные не совпадают!")
                    raise typer.Exit(code=4)

                progress.update(task, advance=1)

        # Вывод результатов
        table = create_table("RSA-32768 Результаты", ["Операция", "Среднее", "Мин", "Макс"])
        table.add_row(
            "Шифрование",
            f"{statistics.mean(encrypt_times):.2f} ms",
            f"{min(encrypt_times):.2f} ms",
            f"{max(encrypt_times):.2f} ms"
        )
        table.add_row(
            "Расшифрование",
            f"{statistics.mean(decrypt_times):.2f} ms",
            f"{min(decrypt_times):.2f} ms",
            f"{max(decrypt_times):.2f} ms"
        )
        console.print(table)
        print_success("\nВсе тесты пройдены успешно!")

    except FileNotFoundError:
        print_error(f"Файл с ключами не найден: {keys}")
        raise typer.Exit(code=1)
    except Exception as e:
        print_error(f"Ошибка тестирования RSA: {e}")
        raise typer.Exit(code=4)


if __name__ == "__main__":
    app()
