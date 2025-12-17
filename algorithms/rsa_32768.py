"""
Реализация RSA-32768 с гарантированной конечностью

Особенности:
- RNG инициализируется один раз на поток
- Явные лимиты и таймауты
- Параллельная генерация p и q
- Оценка времени: 5-20 дней на современном CPU
"""

import os
import sys
import time
import threading
import json
from typing import Optional, Tuple, Dict, Callable
from dataclasses import dataclass, asdict
from concurrent.futures import ProcessPoolExecutor, as_completed, TimeoutError
from pathlib import Path
import math

try:
    import gmpy2
    from gmpy2 import mpz
except ImportError:
    print("ОШИБКА: gmpy2 не установлен", file=sys.stderr)
    print("Установите: pip install gmpy2", file=sys.stderr)
    sys.exit(1)


# Константы и конфигурация

RSA_KEY_SIZE_BITS = 32768
PRIME_SIZE_BITS = 16384
DEFAULT_MILLER_RABIN_ROUNDS = 15
MAX_PRIME_GENERATION_ATTEMPTS = 50000
MAX_PRIME_GENERATION_TIME_HOURS = 72
STANDARD_PUBLIC_EXPONENT = 65537
MAX_MESSAGE_SIZE_BYTES = 4094
PROGRESS_LOG_INTERVAL_SECONDS = 30.0
PROGRESS_LOG_INTERVAL_ATTEMPTS = 10


# Структуры данных

@dataclass
class PrimeGenerationStats:
    """Статистика генерации простого числа"""
    prime: mpz
    attempts: int
    elapsed_seconds: float
    bits: int
    miller_rabin_rounds: int
    avg_check_time_seconds: float

    def to_dict(self) -> dict:
        return {
            'prime': str(self.prime),
            'attempts': self.attempts,
            'elapsed_seconds': self.elapsed_seconds,
            'bits': self.bits,
            'miller_rabin_rounds': self.miller_rabin_rounds,
            'avg_check_time_seconds': self.avg_check_time_seconds
        }


@dataclass
class RSAKeyPair:
    """Пара ключей RSA с метаданными"""
    p: mpz
    q: mpz
    n: mpz
    e: mpz
    d: mpz
    p_stats: PrimeGenerationStats
    q_stats: PrimeGenerationStats
    total_generation_time_seconds: float
    generation_timestamp: float

    def to_dict(self) -> dict:
        return {
            'p': str(self.p),
            'q': str(self.q),
            'n': str(self.n),
            'e': str(self.e),
            'd': str(self.d),
            'p_stats': self.p_stats.to_dict(),
            'q_stats': self.q_stats.to_dict(),
            'total_generation_time_seconds': self.total_generation_time_seconds,
            'generation_timestamp': self.generation_timestamp,
            'key_size_bits': RSA_KEY_SIZE_BITS
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'RSAKeyPair':
        p_stats = PrimeGenerationStats(
            prime=mpz(data['p_stats']['prime']),
            attempts=data['p_stats']['attempts'],
            elapsed_seconds=data['p_stats']['elapsed_seconds'],
            bits=data['p_stats']['bits'],
            miller_rabin_rounds=data['p_stats']['miller_rabin_rounds'],
            avg_check_time_seconds=data['p_stats']['avg_check_time_seconds']
        )
        q_stats = PrimeGenerationStats(
            prime=mpz(data['q_stats']['prime']),
            attempts=data['q_stats']['attempts'],
            elapsed_seconds=data['q_stats']['elapsed_seconds'],
            bits=data['q_stats']['bits'],
            miller_rabin_rounds=data['q_stats']['miller_rabin_rounds'],
            avg_check_time_seconds=data['q_stats']['avg_check_time_seconds']
        )

        return cls(
            p=mpz(data['p']),
            q=mpz(data['q']),
            n=mpz(data['n']),
            e=mpz(data['e']),
            d=mpz(data['d']),
            p_stats=p_stats,
            q_stats=q_stats,
            total_generation_time_seconds=data['total_generation_time_seconds'],
            generation_timestamp=data['generation_timestamp']
        )


# Генерация простых чисел

class PrimeGenerator:
    """Генератор криптографически стойких простых чисел"""

    def __init__(self,
                 miller_rabin_rounds: int = DEFAULT_MILLER_RABIN_ROUNDS,
                 log_callback: Optional[Callable[[str], None]] = None,
                 name: str = ""):
        self.miller_rabin_rounds = miller_rabin_rounds
        self.log = log_callback or print
        self.name = name
        self._init_rng()
        self.log(f"[{self.name}] Генератор инициализирован:")
        self.log(f"  - Miller-Rabin раундов: {miller_rabin_rounds}")
        self.log(f"  - RNG seed: {self.rng_seed_hex[:16]}...")

    def _init_rng(self):
        seed_bytes = os.urandom(32)
        seed_int = int.from_bytes(seed_bytes, byteorder='big')
        self.rand_state = gmpy2.random_state(seed_int)
        self.rng_seed_hex = seed_bytes.hex()

    def generate_prime(self,
                      bits: int,
                      max_attempts: int = MAX_PRIME_GENERATION_ATTEMPTS,
                      max_time_seconds: float = MAX_PRIME_GENERATION_TIME_HOURS * 3600
                      ) -> PrimeGenerationStats:
        self.log(f"\n[{self.name}] Начало генерации {bits}-битного простого числа")
        self.log(f"  - Лимит попыток: {max_attempts:,}")
        self.log(f"  - Лимит времени: {max_time_seconds/3600:.1f} часов")
        self.log(f"  - Ожидаемое количество попыток: ~{bits * math.log(2):.0f}")
        self.log("")

        start_time = time.time()
        last_log_time = start_time
        attempts = 0
        check_times = []
        max_value = mpz(2) ** bits
        high_bit_mask = mpz(1) << (bits - 1)

        try:
            while attempts < max_attempts:
                attempts += 1
                current_time = time.time()
                elapsed = current_time - start_time

                if elapsed > max_time_seconds:
                    raise TimeoutError(
                        f"[{self.name}] Превышен лимит времени: "
                        f"{elapsed/3600:.1f} часов > {max_time_seconds/3600:.1f} часов "
                        f"после {attempts} попыток"
                    )

                time_since_log = current_time - last_log_time
                if (attempts <= 3 or
                    time_since_log >= PROGRESS_LOG_INTERVAL_SECONDS or
                    attempts % PROGRESS_LOG_INTERVAL_ATTEMPTS == 0):

                    rate = attempts / elapsed if elapsed > 0 else 0
                    avg_check = sum(check_times) / len(check_times) if check_times else 0

                    self.log(
                        f"[{self.name}] Попытка {attempts:,}/{max_attempts:,} | "
                        f"Прошло: {elapsed:.0f}с ({elapsed/60:.1f}м) | "
                        f"Скорость: {rate:.2f} проверок/с | "
                        f"Среднее время проверки: {avg_check:.1f}с"
                    )
                    last_log_time = current_time

                candidate = gmpy2.mpz_random(self.rand_state, max_value)
                candidate |= high_bit_mask
                candidate |= mpz(1)

                check_start = time.time()
                is_prime = gmpy2.is_prime(candidate, self.miller_rabin_rounds)
                check_elapsed = time.time() - check_start
                check_times.append(check_elapsed)

                if is_prime:
                    total_elapsed = time.time() - start_time
                    avg_check_time = sum(check_times) / len(check_times)

                    stats = PrimeGenerationStats(
                        prime=candidate,
                        attempts=attempts,
                        elapsed_seconds=total_elapsed,
                        bits=bits,
                        miller_rabin_rounds=self.miller_rabin_rounds,
                        avg_check_time_seconds=avg_check_time
                    )

                    self.log(f"\n[{self.name}] ✓ ПРОСТОЕ ЧИСЛО НАЙДЕНО!")
                    self.log(f"  - Попыток: {attempts:,}")
                    self.log(f"  - Время: {total_elapsed:.1f}с ({total_elapsed/60:.1f}м)")
                    self.log(f"  - Среднее время проверки: {avg_check_time:.2f}с")
                    self.log(f"  - Первые 64 бита: {str(candidate)[:20]}...")

                    return stats

            elapsed = time.time() - start_time
            raise RuntimeError(
                f"[{self.name}] Превышен лимит попыток: {max_attempts:,} попыток "
                f"за {elapsed/3600:.2f} часов. Возможна проблема с RNG."
            )

        except KeyboardInterrupt:
            elapsed = time.time() - start_time
            self.log(f"\n[{self.name}] Прервано пользователем после {attempts} попыток ({elapsed:.0f}с)")
            raise
        except Exception as e:
            elapsed = time.time() - start_time
            self.log(f"\n[{self.name}] ОШИБКА после {attempts} попыток ({elapsed:.0f}с): {e}")
            raise


# Параллельная генерация

def _generate_prime_worker(bits: int,
                          miller_rabin_rounds: int,
                          name: str,
                          max_attempts: int,
                          max_time_seconds: float) -> Dict:
    """Worker-функция для параллельной генерации"""
    generator = PrimeGenerator(
        miller_rabin_rounds=miller_rabin_rounds,
        log_callback=lambda msg: print(f"[Процесс {name}] {msg}", flush=True),
        name=name
    )

    stats = generator.generate_prime(
        bits=bits,
        max_attempts=max_attempts,
        max_time_seconds=max_time_seconds
    )

    return stats.to_dict()


def generate_prime_pair_parallel(
    bits: int = PRIME_SIZE_BITS,
    miller_rabin_rounds: int = DEFAULT_MILLER_RABIN_ROUNDS,
    max_attempts: int = MAX_PRIME_GENERATION_ATTEMPTS,
    max_time_hours: float = MAX_PRIME_GENERATION_TIME_HOURS
) -> Tuple[PrimeGenerationStats, PrimeGenerationStats]:
    print("\n" + "="*80)
    print("ПАРАЛЛЕЛЬНАЯ ГЕНЕРАЦИЯ ПРОСТЫХ ЧИСЕЛ")
    print("="*80)
    print(f"Конфигурация:")
    print(f"  - Размер каждого простого: {bits} бит")
    print(f"  - Miller-Rabin раундов: {miller_rabin_rounds}")
    print(f"  - Максимум попыток на число: {max_attempts:,}")
    print(f"  - Максимум времени на число: {max_time_hours} часов")
    print(f"\nЗапуск двух независимых процессов для генерации p и q...")
    print("="*80)

    max_time_seconds = max_time_hours * 3600
    start_time = time.time()

    with ProcessPoolExecutor(max_workers=2) as executor:
        future_p = executor.submit(
            _generate_prime_worker,
            bits, miller_rabin_rounds, "p", max_attempts, max_time_seconds
        )
        future_q = executor.submit(
            _generate_prime_worker,
            bits, miller_rabin_rounds, "q", max_attempts, max_time_seconds
        )

        timeout_seconds = max_time_seconds + 300

        try:
            p_dict = future_p.result(timeout=timeout_seconds)
            q_dict = future_q.result(timeout=timeout_seconds)
        except TimeoutError:
            print("\n" + "="*80)
            print("КРИТИЧЕСКАЯ ОШИБКА: Превышен общий лимит времени!")
            print("="*80)
            executor.shutdown(wait=False, cancel_futures=True)
            raise

    p_stats = PrimeGenerationStats(
        prime=mpz(p_dict['prime']),
        attempts=p_dict['attempts'],
        elapsed_seconds=p_dict['elapsed_seconds'],
        bits=p_dict['bits'],
        miller_rabin_rounds=p_dict['miller_rabin_rounds'],
        avg_check_time_seconds=p_dict['avg_check_time_seconds']
    )
    q_stats = PrimeGenerationStats(
        prime=mpz(q_dict['prime']),
        attempts=q_dict['attempts'],
        elapsed_seconds=q_dict['elapsed_seconds'],
        bits=q_dict['bits'],
        miller_rabin_rounds=q_dict['miller_rabin_rounds'],
        avg_check_time_seconds=q_dict['avg_check_time_seconds']
    )

    total_time = time.time() - start_time

    print("\n" + "="*80)
    print("ПАРАЛЛЕЛЬНАЯ ГЕНЕРАЦИЯ ЗАВЕРШЕНА")
    print("="*80)
    print(f"Результаты:")
    print(f"  p: {p_stats.attempts:,} попыток за {p_stats.elapsed_seconds/60:.1f} минут")
    print(f"  q: {q_stats.attempts:,} попыток за {q_stats.elapsed_seconds/60:.1f} минут")
    print(f"  Общее время (параллельно): {total_time/60:.1f} минут")
    print(f"  Экономия времени: {(p_stats.elapsed_seconds + q_stats.elapsed_seconds - total_time)/60:.1f} минут")
    print(f"  Ускорение: {(p_stats.elapsed_seconds + q_stats.elapsed_seconds)/total_time:.2f}x")
    print("="*80)

    return p_stats, q_stats


# RSA класс

class RSA32768:
    """Реализация RSA-32768 с поддержкой сохранения/загрузки ключей"""

    def __init__(self, keypair: Optional[RSAKeyPair] = None, public_key: Optional[Dict] = None, private_key: Optional[Dict] = None):
        """
        Инициализация RSA32768

        Args:
            keypair: Полный объект RSAKeyPair
            public_key: Словарь с 'n' и 'e' (для шифрования)
            private_key: Словарь с 'd', 'p', 'q' (для расшифрования)
        """
        if keypair:
            self.keypair = keypair
        elif public_key or private_key:
            # Создание минимального keypair для совместимости
            @dataclass
            class MinimalKeyPair:
                n: mpz
                e: mpz
                d: Optional[mpz] = None
                p: Optional[mpz] = None
                q: Optional[mpz] = None

            n = mpz(public_key['n']) if public_key else None
            e = mpz(public_key['e']) if public_key else None
            d = mpz(private_key['d']) if private_key and 'd' in private_key else None
            p = mpz(private_key['p']) if private_key and 'p' in private_key else None
            q = mpz(private_key['q']) if private_key and 'q' in private_key else None

            self.keypair = MinimalKeyPair(n=n, e=e, d=d, p=p, q=q)
        else:
            raise ValueError(
                "RSA32768 требует явной передачи ключей. "
                "Используйте RSA32768.generate_keys() для генерации новых ключей."
            )

    @classmethod
    def generate_keys(cls,
                     miller_rabin_rounds: int = DEFAULT_MILLER_RABIN_ROUNDS,
                     max_attempts: int = MAX_PRIME_GENERATION_ATTEMPTS,
                     max_time_hours: float = MAX_PRIME_GENERATION_TIME_HOURS,
                     save_to: Optional[Path] = None) -> 'RSA32768':
        print("\n" + "="*80)
        print("ГЕНЕРАЦИЯ КЛЮЧЕЙ RSA-32768")
        print("="*80)
        print("РЕАЛИСТИЧНАЯ ОЦЕНКА ВРЕМЕНИ:")
        print(f"  - Miller-Rabin раундов: {miller_rabin_rounds}")
        print(f"  - Ожидаемых попыток на простое число: ~11,356")
        print(f"  - Время проверки одного числа: 30-120 секунд")
        print(f"  - Время генерации одного простого: 4-15 дней")
        print(f"  - ОБЩЕЕ ВРЕМЯ (параллельно): 5-20 дней")
        print("="*80)
        print()

        input("Нажмите Enter для подтверждения начала генерации или Ctrl+C для отмены...")

        generation_start = time.time()

        p_stats, q_stats = generate_prime_pair_parallel(
            bits=PRIME_SIZE_BITS,
            miller_rabin_rounds=miller_rabin_rounds,
            max_attempts=max_attempts,
            max_time_hours=max_time_hours
        )

        p = p_stats.prime
        q = q_stats.prime

        print("\nПроверка уникальности p и q...")
        if p == q:
            raise RuntimeError("КРИТИЧЕСКАЯ ОШИБКА: p == q!")
        print("✓ p ≠ q")

        print("Вычисление n = p × q...")
        n = p * q
        n_bits = n.bit_length()
        print(f"✓ n вычислен ({n_bits} бит)")

        if n_bits != RSA_KEY_SIZE_BITS:
            print(f"  ПРЕДУПРЕЖДЕНИЕ: Размер n = {n_bits} бит, ожидалось {RSA_KEY_SIZE_BITS} бит")

        print("Вычисление φ(n) = (p-1)(q-1)...")
        phi_n = (p - 1) * (q - 1)
        print("✓ φ(n) вычислен")

        print(f"Выбор открытой экспоненты e = {STANDARD_PUBLIC_EXPONENT}...")
        e = mpz(STANDARD_PUBLIC_EXPONENT)

        gcd_val = gmpy2.gcd(e, phi_n)
        if gcd_val != 1:
            raise RuntimeError(f"ОШИБКА: gcd(e, φ(n)) = {gcd_val} ≠ 1")
        print("✓ gcd(e, φ(n)) = 1")

        print("Вычисление секретной экспоненты d = e⁻¹ mod φ(n)...")
        d = gmpy2.invert(e, phi_n)
        print("✓ d вычислен")

        print("Верификация ключей: ed ≡ 1 (mod φ(n))...")
        verification = (e * d) % phi_n
        if verification != 1:
            raise RuntimeError(f"ОШИБКА ВЕРИФИКАЦИИ: (e×d) mod φ(n) = {verification} ≠ 1")
        print("✓ Ключи верифицированы")

        total_time = time.time() - generation_start
        keypair = RSAKeyPair(
            p=p,
            q=q,
            n=n,
            e=e,
            d=d,
            p_stats=p_stats,
            q_stats=q_stats,
            total_generation_time_seconds=total_time,
            generation_timestamp=time.time()
        )

        print("\n" + "="*80)
        print("ГЕНЕРАЦИЯ КЛЮЧЕЙ ЗАВЕРШЕНА УСПЕШНО!")
        print("="*80)
        print(f"Общее время: {total_time/3600:.2f} часов ({total_time/86400:.2f} дней)")
        print(f"Размер n: {n_bits} бит")
        print("="*80)

        if save_to:
            print(f"\nСохранение ключей в {save_to}...")
            cls._save_keypair(keypair, save_to)
            print("✓ Ключи сохранены")

        return cls(keypair=keypair)

    @classmethod
    def load_keys(cls, path: Path) -> 'RSA32768':
        """Загрузка ключей из файла"""
        print(f"Загрузка ключей из {path}...")

        if not path.exists():
            raise FileNotFoundError(f"Файл ключей не найден: {path}")

        with open(path, 'r') as f:
            data = json.load(f)

        keypair = RSAKeyPair.from_dict(data)
        print("✓ Ключи загружены")

        return cls(keypair=keypair)

    @staticmethod
    def _save_keypair(keypair: RSAKeyPair, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(keypair.to_dict(), f, indent=2)

    def save_keys(self, path: Path):
        self._save_keypair(self.keypair, path)

    def encrypt(self, message: bytes) -> bytes:
        if len(message) > MAX_MESSAGE_SIZE_BYTES:
            raise ValueError(f"Сообщение слишком большое: {len(message)} > {MAX_MESSAGE_SIZE_BYTES}")

        buf = bytearray(4096)
        pad_len = 4096 - len(message)
        buf[2] = (pad_len // 256) & 0xFF
        buf[3] = pad_len % 256
        buf[pad_len:] = message
        m = mpz(int.from_bytes(buf, byteorder='big'))

        if m >= self.keypair.n:
            raise ValueError("Сообщение слишком велико для модуля n")

        c = gmpy2.powmod(m, self.keypair.e, self.keypair.n)
        return c.to_bytes(4096, byteorder='big')

    def decrypt(self, ciphertext: bytes) -> bytes:
        if len(ciphertext) != 4096:
            raise ValueError(f"Неверный размер шифртекста: {len(ciphertext)} ≠ 4096")

        c = mpz(int.from_bytes(ciphertext, byteorder='big'))
        m = gmpy2.powmod(c, self.keypair.d, self.keypair.n)
        m_bytes = m.to_bytes(4096, byteorder='big')
        pad_len = (m_bytes[2] * 256) + m_bytes[3]
        return bytes(m_bytes[pad_len:])


# Диагностика окружения

def diagnose_environment():
    print("\n" + "="*80)
    print("ДИАГНОСТИКА ОКРУЖЕНИЯ")
    print("="*80)

    print("\n[1] Проверка gmpy2:")
    print(f"  ✓ gmpy2 версия: {gmpy2.version()}")
    print(f"  ✓ GMP версия: {gmpy2.mp_version()}")
    print(f"  ✓ MPFR версия: {gmpy2.mpfr_version()}")
    print(f"  ✓ MPC версия: {gmpy2.mpc_version()}")

    print("\n[2] Проверка архитектуры:")
    import platform
    import struct
    print(f"  Система: {platform.system()}")
    print(f"  Машина: {platform.machine()}")
    print(f"  Процессор: {platform.processor()}")
    print(f"  Python: {platform.python_version()}")
    print(f"  Разрядность: {struct.calcsize('P') * 8} бит")

    if platform.system() in ['Linux', 'Darwin']:
        print("\n[3] Проверка нативности библиотек:")
        try:
            import subprocess
            gmpy2_path = gmpy2.__file__
            result = subprocess.run(['file', gmpy2_path], capture_output=True, text=True)

            if result.returncode == 0:
                output = result.stdout
                print(f"  gmpy2 путь: {gmpy2_path}")
                print(f"  Информация: {output.strip()}")

                if platform.system() == 'Darwin' and platform.machine() == 'arm64':
                    if 'arm64' in output or 'arm64e' in output:
                        print("  ✓ gmpy2 скомпилирован для ARM64 (нативно)")
                    elif 'x86_64' in output:
                        print("  ⚠ ПРЕДУПРЕЖДЕНИЕ: gmpy2 скомпилирован для x86_64!")
                        print("    Будет работать через Rosetta 2 (медленнее в 2-5x)")
                        print("    Рекомендация: переустановить gmpy2 с нативной сборкой")
        except Exception as e:
            print(f"  Не удалось проверить: {e}")

    print("\n[4] Тест производительности:")
    test_bits = 512
    print(f"  Генерация {test_bits}-битного простого числа (3 попытки)...")

    times = []
    for i in range(3):
        gen = PrimeGenerator(
            miller_rabin_rounds=15,
            log_callback=lambda _: None,
            name=f"test{i}"
        )
        start = time.time()
        stats = gen.generate_prime(test_bits, max_attempts=10000, max_time_seconds=60)
        elapsed = time.time() - start
        times.append(elapsed)
        print(f"    Попытка {i+1}: {stats.attempts} проверок за {elapsed:.3f}с")

    avg_time = sum(times) / len(times)
    print(f"  Среднее время: {avg_time:.3f}с")

    ratio = (PRIME_SIZE_BITS / test_bits) ** 3
    expected_check_time = avg_time * ratio
    expected_attempts = PRIME_SIZE_BITS * math.log(2)
    estimated_total_days = (expected_check_time * expected_attempts) / 86400

    print(f"\n[5] Экстраполяция для RSA-32768:")
    print(f"  Оценка времени проверки одного {PRIME_SIZE_BITS}-битного числа: {expected_check_time:.1f}с")
    print(f"  Ожидаемое количество попыток: {expected_attempts:.0f}")
    print(f"  ОЦЕНКА времени генерации одного простого: {estimated_total_days:.1f} дней")
    print(f"  ОЦЕНКА времени генерации пары (параллельно): {estimated_total_days:.1f} дней")

    print("\n" + "="*80)
    print("Диагностика завершена")
    print("="*80)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Надёжная генерация ключей RSA-32768',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--diagnose', action='store_true',
                       help='Диагностика окружения')
    parser.add_argument('--generate', action='store_true',
                       help='Генерация новых ключей')
    parser.add_argument('--rounds', type=int, default=DEFAULT_MILLER_RABIN_ROUNDS,
                       help=f'Количество раундов Miller-Rabin (по умолчанию: {DEFAULT_MILLER_RABIN_ROUNDS})')
    parser.add_argument('--output', type=Path, default=Path('rsa32768_keys.json'),
                       help='Путь для сохранения ключей')

    args = parser.parse_args()

    if args.diagnose:
        diagnose_environment()
    elif args.generate:
        rsa = RSA32768.generate_keys(
            miller_rabin_rounds=args.rounds,
            save_to=args.output
        )
        print(f"\nКлючи сохранены в: {args.output}")
    else:
        parser.print_help()
