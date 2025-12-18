"""
Утилиты для CLI
"""

import json
import base64
import binascii
from pathlib import Path
from typing import Any, Optional
from datetime import datetime

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich import print as rprint

console = Console()


def format_time(seconds: float) -> str:
    """Форматирование времени в читаемый вид"""
    if seconds < 60:
        return f"{seconds:.2f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.1f}s"
    elif seconds < 86400:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"
    else:
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        return f"{days}d {hours}h"


def encode_data(data: bytes, encoding: str = "base64") -> str:
    """Кодирование данных в строку"""
    if encoding == "base64":
        return base64.b64encode(data).decode('utf-8')
    elif encoding == "hex":
        return data.hex()
    else:
        raise ValueError(f"Неподдерживаемая кодировка: {encoding}")


def decode_data(data: str, encoding: str = "base64") -> bytes:
    """Декодирование данных из строки"""
    if encoding == "base64":
        return base64.b64decode(data)
    elif encoding == "hex":
        return bytes.fromhex(data)
    else:
        raise ValueError(f"Неподдерживаемая кодировка: {encoding}")


def load_json_file(file_path: Path) -> dict:
    """Загрузка JSON файла"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        console.print(f"[red]Ошибка: Файл {file_path} не найден[/red]")
        raise
    except json.JSONDecodeError as e:
        console.print(f"[red]Ошибка парсинга JSON: {e}[/red]")
        raise


def save_json_file(data: dict, file_path: Path, pretty: bool = True) -> None:
    """Сохранение данных в JSON файл"""
    with open(file_path, 'w', encoding='utf-8') as f:
        if pretty:
            json.dump(data, f, indent=2, ensure_ascii=False)
        else:
            json.dump(data, f, ensure_ascii=False)


def print_success(message: str) -> None:
    """Вывод сообщения об успехе"""
    console.print(f"[green]✓[/green] {message}")


def print_error(message: str) -> None:
    """Вывод сообщения об ошибке"""
    console.print(f"[red]✗[/red] {message}")


def print_warning(message: str) -> None:
    """Вывод предупреждения"""
    console.print(f"[yellow]⚠[/yellow] {message}")


def print_info(message: str) -> None:
    """Вывод информационного сообщения"""
    console.print(f"[blue]ℹ[/blue] {message}")


def print_json(data: Any, title: Optional[str] = None) -> None:
    """Красивый вывод JSON"""
    if title:
        console.print(f"\n[bold]{title}[/bold]")
    console.print_json(json.dumps(data, ensure_ascii=False, indent=2))


def create_table(title: str, columns: list[str]) -> Table:
    """Создание Rich таблицы"""
    table = Table(title=title, show_header=True, header_style="bold magenta")
    for col in columns:
        table.add_column(col)
    return table


def create_progress() -> Progress:
    """Создание прогресс-бара"""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console
    )


def read_input_data(input_str: str, force_file: bool = False, force_text: bool = False) -> bytes:
    """
    Чтение данных с явным контролем источника

    Args:
        input_str: Строка или путь к файлу
        force_file: Принудительно читать как файл
        force_text: Принудительно читать как текст

    Returns:
        Данные в байтах

    Raises:
        FileNotFoundError: Если файл не найден при force_file=True
        ValueError: Если указаны оба флага одновременно
    """
    if force_file and force_text:
        raise ValueError("Нельзя указать --file и --text одновременно")

    if force_file:
        # Принудительно читаем как файл
        file_path = Path(input_str)
        if not file_path.exists():
            raise FileNotFoundError(f"Файл не найден: {file_path}")
        with open(file_path, 'rb') as f:
            return f.read()
    elif force_text:
        # Принудительно читаем как текст
        return input_str.encode('utf-8')
    else:
        # Автоопределение: проверяем существование файла
        file_path = Path(input_str)
        if file_path.exists():
            with open(file_path, 'rb') as f:
                return f.read()
        else:
            return input_str.encode('utf-8')


def format_bytes(size: int) -> str:
    """Форматирование размера в байтах"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} TB"


def get_timestamp() -> str:
    """Получение текущего timestamp в ISO формате"""
    return datetime.utcnow().isoformat() + 'Z'


def validate_data_size(data: bytes, max_size: int, algorithm: str) -> None:
    """Валидация размера данных"""
    size = len(data)
    if size > max_size:
        raise ValueError(
            f"Размер данных ({format_bytes(size)}) превышает "
            f"максимальный для {algorithm} ({format_bytes(max_size)})"
        )


def check_gmpy2_available() -> bool:
    """Проверка доступности gmpy2"""
    try:
        import gmpy2
        return True
    except ImportError:
        return False


def require_gmpy2() -> None:
    """Проверка наличия gmpy2, вывод ошибки если отсутствует"""
    if not check_gmpy2_available():
        print_error("gmpy2 не установлен - необходим для RSA операций")
        print_info("Установите: pip install gmpy2")
        console.print("\nУстановка на разных платформах:")
        console.print("  macOS:         brew install gmp && pip install gmpy2")
        console.print("  Ubuntu/Debian: sudo apt-get install libgmp-dev && pip install gmpy2")
        raise ImportError("gmpy2 not available")
