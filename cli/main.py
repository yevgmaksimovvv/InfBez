#!/usr/bin/env python3
"""
InfBez CLI - Главный файл
"""

import typer
from typing import Optional
from pathlib import Path

from cli import __version__
from cli.utils import console, print_info
from cli.commands import crypto, keys, test, server

# Создание главного приложения
app = typer.Typer(
    name="infbez",
    help="InfBez CLI - Криптографический интерфейс командной строки",
    add_completion=True,
    rich_markup_mode="rich",
)

# Регистрация подкоманд
app.add_typer(crypto.app, name="crypto", help="Криптографические операции (encrypt, decrypt, hash)")
app.add_typer(keys.app, name="keys", help="Управление RSA ключами (generate, list, export, import)")
app.add_typer(test.app, name="test", help="Тестирование и бенчмарки алгоритмов")
app.add_typer(server.app, name="server", help="Управление backend сервером")


def version_callback(value: bool):
    """Callback для вывода версии"""
    if value:
        console.print(f"InfBez CLI версия {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Показать версию CLI"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Подробный вывод"
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet",
        "-q",
        help="Минимальный вывод"
    ),
):
    """
    InfBez CLI - Криптографический интерфейс командной строки

    Используйте подкоманды для выполнения операций:

    • crypto  - Шифрование, расшифрование, хеширование
    • keys    - Управление RSA ключами
    • test    - Тестирование алгоритмов
    • server  - Управление backend сервером

    Примеры:

      infbez crypto encrypt "Hello" -a kuznechik
      infbez keys generate -o my_keys.json
      infbez test benchmark --progress
      infbez server start --reload
    """
    # Глобальные настройки (можно использовать через context)
    if verbose:
        console.print("[dim]Verbose mode enabled[/dim]")


if __name__ == "__main__":
    app()
