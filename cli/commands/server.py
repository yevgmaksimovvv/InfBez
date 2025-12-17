"""
Команды для управления backend сервером
"""

import typer
from pathlib import Path
import sys
import subprocess
import os

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cli.utils import (
    console, print_success, print_error, print_warning, print_info
)

app = typer.Typer(help="Управление backend сервером")


@app.command("start")
def start(
    host: str = typer.Option(
        "127.0.0.1",
        "--host", "-h",
        help="Хост для запуска сервера"
    ),
    port: int = typer.Option(
        8000,
        "--port", "-p",
        min=1, max=65535,
        help="Порт для запуска сервера"
    ),
    reload: bool = typer.Option(
        False,
        "--reload", "-r",
        help="Автоперезагрузка (development режим)"
    ),
    workers: int = typer.Option(
        1,
        "--workers", "-w",
        min=1, max=16,
        help="Количество worker процессов"
    ),
):
    """
    Запуск FastAPI сервера

    Примеры:

      # Development режим
      infbez server start --reload

      # Production режим
      infbez server start -h 0.0.0.0 -p 8000 -w 4
    """
    try:
        backend_dir = Path(__file__).parent.parent.parent / "backend"

        if not backend_dir.exists():
            print_error(f"Backend директория не найдена: {backend_dir}")
            raise typer.Exit(code=1)

        # Проверка .env файла
        env_file = backend_dir / ".env"
        if not env_file.exists():
            print_warning(".env файл не найден!")
            print_info("Создайте .env файл в директории backend/ на основе .env.example")
            if not typer.confirm("Продолжить без .env файла?"):
                raise typer.Exit()

        console.print(f"\n[bold green]Запуск InfBez сервера...[/bold green]")
        print_info(f"Host: {host}:{port}")
        print_info(f"Reload: {'✓' if reload else '✗'}")
        print_info(f"Workers: {workers}")
        console.print()

        # Формирование команды
        cmd = [
            "uvicorn",
            "main:app",
            "--host", host,
            "--port", str(port),
        ]

        if reload:
            cmd.append("--reload")
        else:
            cmd.extend(["--workers", str(workers)])

        # Запуск сервера
        subprocess.run(cmd, cwd=backend_dir, check=True)

    except KeyboardInterrupt:
        print_info("\nСервер остановлен")
    except subprocess.CalledProcessError as e:
        print_error(f"Ошибка запуска сервера: {e}")
        raise typer.Exit(code=1)
    except FileNotFoundError:
        print_error("uvicorn не найден. Установите: pip install uvicorn")
        raise typer.Exit(code=1)


@app.command("init")
def init_db(
    force: bool = typer.Option(
        False,
        "--force", "-f",
        help="Пересоздать таблицы (УДАЛИТ все данные!)"
    ),
):
    """
    Инициализация базы данных

    Примеры:

      infbez server init
      infbez server init --force  # Пересоздать таблицы
    """
    try:
        backend_dir = Path(__file__).parent.parent.parent / "backend"

        if force:
            print_warning("ВНИМАНИЕ: Все данные в БД будут УДАЛЕНЫ!")
            if not typer.confirm("Продолжить?"):
                print_info("Операция отменена")
                raise typer.Exit()

        console.print("\n[bold cyan]Инициализация базы данных...[/bold cyan]\n")

        # Проверка наличия migration_helper.py
        migration_script = backend_dir / "migration_helper.py"
        if migration_script.exists():
            cmd = ["python", "migration_helper.py"]
            subprocess.run(cmd, cwd=backend_dir, check=True)
            print_success("База данных инициализирована успешно")
        else:
            # Альтернативный способ через Python
            print_info("Создание таблиц через SQLAlchemy...")

            # Импорт моделей и создание таблиц
            sys.path.insert(0, str(backend_dir))
            try:
                from core.database import engine, Base
                from models import user, rsa_keypair, document

                if force:
                    Base.metadata.drop_all(bind=engine)
                    print_warning("Старые таблицы удалены")

                Base.metadata.create_all(bind=engine)
                print_success("Таблицы созданы: users, rsa_keypairs, documents")

            except ImportError as e:
                print_error(f"Ошибка импорта моделей: {e}")
                print_info("Убедитесь, что backend зависимости установлены")
                raise typer.Exit(code=5)

    except subprocess.CalledProcessError as e:
        print_error(f"Ошибка инициализации БД: {e}")
        raise typer.Exit(code=5)
    except Exception as e:
        print_error(f"Ошибка: {e}")
        raise typer.Exit(code=1)


@app.command("config")
def show_config():
    """
    Показать текущую конфигурацию сервера

    Примеры:

      infbez server config
    """
    try:
        backend_dir = Path(__file__).parent.parent.parent / "backend"
        env_file = backend_dir / ".env"

        console.print("\n[bold cyan]Конфигурация InfBez Server[/bold cyan]\n")

        if not env_file.exists():
            print_warning(".env файл не найден")
            print_info(f"Создайте файл: {env_file}")
            print_info("На основе: .env.example")
            raise typer.Exit()

        # Чтение .env
        config = {}
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key] = value

        # Вывод конфигурации (скрываем секреты)
        from rich.panel import Panel
        from rich.table import Table

        table = Table(show_header=False, box=None)
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="yellow")

        for key, value in config.items():
            # Скрываем секретные значения
            if any(secret in key.upper() for secret in ['SECRET', 'KEY', 'PASSWORD']):
                display_value = '*' * min(len(value), 32) + f" ({len(value)} chars)"
            else:
                display_value = value

            table.add_row(key, display_value)

        console.print(Panel(table, title="Environment Configuration", border_style="green"))

        # Проверка подключения к БД
        console.print("\n[bold]Database Connection:[/bold]")
        try:
            sys.path.insert(0, str(backend_dir))
            from core.database import engine
            from sqlalchemy import text

            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                print_success("Подключение к БД активно")

        except Exception as e:
            print_error(f"Ошибка подключения к БД: {e}")

    except Exception as e:
        print_error(f"Ошибка чтения конфигурации: {e}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
