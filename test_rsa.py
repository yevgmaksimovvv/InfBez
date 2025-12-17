#!/usr/bin/env python3
"""Тестирование RSA-32768"""

import sys
import os
import time
import argparse
from pathlib import Path

algorithms_path = os.path.join(os.path.dirname(__file__), 'algorithms')
sys.path.insert(0, algorithms_path)

try:
    from rsa_32768 import (
        RSA32768,
        diagnose_environment,
        DEFAULT_MILLER_RABIN_ROUNDS,
        MAX_MESSAGE_SIZE_BYTES
    )
except ImportError as e:
    print(f"❌ ОШИБКА: Не удалось импортировать модуль RSA: {e}")
    print("Убедитесь, что gmpy2 установлен: pip install gmpy2")
    sys.exit(1)


def format_time(seconds: float) -> str:
    """Форматирование времени"""
    if seconds < 1:
        return f"{seconds * 1000:.2f} мс"
    elif seconds < 60:
        return f"{seconds:.2f} с"
    elif seconds < 3600:
        return f"{seconds / 60:.2f} мин"
    else:
        return f"{seconds / 3600:.2f} ч"


def test_encryption_decryption(rsa: RSA32768, test_data: bytes, iterations: int = 5):
    """Тестирование шифрования/расшифрования"""
    print(f"\n{'='*80}")
    print(f"ТЕСТ ШИФРОВАНИЯ/РАСШИФРОВАНИЯ ({len(test_data)} байт данных)")
    print(f"{'='*80}")

    if len(test_data) > MAX_MESSAGE_SIZE_BYTES:
        print(f"⚠️  Данные слишком большие: {len(test_data)} > {MAX_MESSAGE_SIZE_BYTES} байт")
        print("Обрезка до максимального размера...")
        test_data = test_data[:MAX_MESSAGE_SIZE_BYTES]

    encrypt_times = []
    decrypt_times = []

    print(f"Выполнение {iterations} итераций...")

    for i in range(iterations):
        start = time.perf_counter()
        ciphertext = rsa.encrypt(test_data)
        encrypt_time = time.perf_counter() - start
        encrypt_times.append(encrypt_time)

        start = time.perf_counter()
        plaintext = rsa.decrypt(ciphertext)
        decrypt_time = time.perf_counter() - start
        decrypt_times.append(decrypt_time)

        if plaintext != test_data:
            print(f"❌ ОШИБКА в итерации {i+1}: Данные не совпадают!")
            return False

        if i == 0 or (i + 1) % max(1, iterations // 5) == 0:
            print(f"  Итерация {i+1}/{iterations}: "
                  f"шифр={format_time(encrypt_time)}, "
                  f"расшифр={format_time(decrypt_time)}")

    avg_encrypt = sum(encrypt_times) / len(encrypt_times)
    avg_decrypt = sum(decrypt_times) / len(decrypt_times)
    min_encrypt = min(encrypt_times)
    max_encrypt = max(encrypt_times)
    min_decrypt = min(decrypt_times)
    max_decrypt = max(decrypt_times)

    print(f"\n{'='*80}")
    print("РЕЗУЛЬТАТЫ:")
    print(f"{'='*80}")
    print(f"Шифрование:")
    print(f"  Среднее: {format_time(avg_encrypt)}")
    print(f"  Минимум: {format_time(min_encrypt)}")
    print(f"  Максимум: {format_time(max_encrypt)}")
    print(f"  Скорость: {len(test_data) / avg_encrypt / 1024:.2f} КБ/с")

    print(f"\nРасшифрование:")
    print(f"  Среднее: {format_time(avg_decrypt)}")
    print(f"  Минимум: {format_time(min_decrypt)}")
    print(f"  Максимум: {format_time(max_decrypt)}")
    print(f"  Скорость: {len(test_data) / avg_decrypt / 1024:.2f} КБ/с")

    print(f"\n✓ Все {iterations} итераций прошли успешно")
    print(f"{'='*80}")

    return True


def main():
    parser = argparse.ArgumentParser(
        description='Тестирование надёжной реализации RSA-32768',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры:
  python test_rsa.py --diagnose
  python test_rsa.py --generate --keys keys.json --rounds 15
  python test_rsa.py --test --keys keys.json --iterations 10
  python test_rsa.py --generate --test --keys keys.json

ВАЖНО: Генерация ключей RSA-32768 займёт 5-20 дней!
        """
    )

    parser.add_argument('--diagnose', action='store_true',
                       help='Диагностика окружения (проверка gmpy2, архитектуры, производительности)')
    parser.add_argument('--generate', action='store_true',
                       help='Генерация новых ключей RSA-32768')
    parser.add_argument('--test', action='store_true',
                       help='Тестирование шифрования/расшифрования')

    parser.add_argument('--keys', type=str, default='rsa32768_keys.json',
                       help='Путь к файлу с ключами (по умолчанию: rsa32768_keys.json)')
    parser.add_argument('--rounds', type=int, default=DEFAULT_MILLER_RABIN_ROUNDS,
                       help=f'Количество раундов Miller-Rabin (по умолчанию: {DEFAULT_MILLER_RABIN_ROUNDS})')
    parser.add_argument('--iterations', type=int, default=5,
                       help='Количество итераций тестирования (по умолчанию: 5)')
    parser.add_argument('--data-size', type=int, default=1024,
                       help='Размер тестовых данных в байтах (по умолчанию: 1024)')

    args = parser.parse_args()

    if not any([args.diagnose, args.generate, args.test]):
        parser.print_help()
        return

    if args.diagnose:
        diagnose_environment()
        return

    keys_path = Path(args.keys)
    rsa = None
    if args.generate:
        print(f"\n{'='*80}")
        print("ГЕНЕРАЦИЯ КЛЮЧЕЙ RSA-32768")
        print(f"{'='*80}")

        try:
            rsa = RSA32768.generate_keys(
                miller_rabin_rounds=args.rounds,
                save_to=keys_path
            )
            print(f"\n✓ Ключи сгенерированы и сохранены в {keys_path}")

        except KeyboardInterrupt:
            print("\n\n⚠️  Генерация прервана пользователем (Ctrl+C)")
            return
        except Exception as e:
            print(f"\n\n❌ ОШИБКА при генерации: {e}")
            import traceback
            traceback.print_exc()
            return

    if args.test:
        if rsa is None:
            if not keys_path.exists():
                print(f"\n❌ ОШИБКА: Файл ключей не найден: {keys_path}")
                print("Сначала сгенерируйте ключи с помощью --generate")
                return

            try:
                print(f"\nЗагрузка ключей из {keys_path}...")
                rsa = RSA32768.load_keys(keys_path)
                print("✓ Ключи загружены")
            except Exception as e:
                print(f"❌ ОШИБКА при загрузке ключей: {e}")
                return

        print(f"\nГенерация тестовых данных ({args.data_size} байт)...")
        test_data = os.urandom(min(args.data_size, MAX_MESSAGE_SIZE_BYTES))

        success = test_encryption_decryption(rsa, test_data, args.iterations)

        if success:
            print("\n✓ Все тесты пройдены успешно!")
        else:
            print("\n❌ Тесты провалены!")
            return

    print(f"\n{'='*80}")
    print("ЗАВЕРШЕНО")
    print(f"{'='*80}")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nПрограмма прервана пользователем")
        sys.exit(130)
