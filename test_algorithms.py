#!/usr/bin/env python3
"""
CLI утилита для тестирования криптографических алгоритмов с замером времени
"""
import sys
import os
import time
import argparse
import threading
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

# Проверка наличия библиотеки tqdm для отображения прогресса
try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False

# Добавление пути к модулю algorithms
algorithms_path = os.path.join(os.path.dirname(__file__), 'algorithms')
sys.path.insert(0, algorithms_path)

from kuznechik.kuznechik import Kuznechik
from streebog.streebog import streebog_512

# Проверка доступности модуля RSA (требуется установленная библиотека gmpy2)
RSA_AVAILABLE = False
RSA32768 = None
try:
    from rsa_32768 import RSA32768
    RSA_AVAILABLE = True
except ImportError:
    RSA_AVAILABLE = False


class SimpleProgressBar:
    """Простой текстовый индикатор прогресса без внешних зависимостей"""
    def __init__(self, total: Optional[int], desc: str = "", width: int = 40):
        self.total = total
        self.current = 0
        self.desc = desc
        self.width = width
        self.start_time = time.time()
        self._displayed = False
    
    def update(self, n: int = 1):
        """Обновить прогресс на n шагов"""
        self.current += n
        if self.total is not None:
            self.current = min(self.current, self.total)
        self._display()
    
    def set_description(self, desc: str):
        """Изменить описание"""
        self.desc = desc
    
    def _display(self):
        """Отображение индикатора прогресса"""
        if self.total is None:
            # Неизвестное общее количество шагов - показываем только текущее значение
            percent = 0
            bar = '█' * (self.current % self.width) + '░' * (self.width - (self.current % self.width))
            status = f"{self.current} попыток"
        elif self.total == 0:
            percent = 100
            bar = '█' * self.width
            status = f"{self.current}/{self.total}"
        else:
            percent = int(100 * self.current / self.total)
            filled = int(self.width * self.current / self.total)
            bar = '█' * filled + '░' * (self.width - filled)
            status = f"{self.current}/{self.total}"
        
        elapsed = time.time() - self.start_time
        if self.current > 0:
            rate = self.current / elapsed
            if self.total is not None and self.total > self.current:
                eta = (self.total - self.current) / rate if rate > 0 else 0
                eta_str = f"ETA: {eta:.1f}s" if eta > 0 else "ETA: --"
            else:
                eta_str = f"({elapsed:.1f}s)"
        else:
            eta_str = ""
        
        print(f"\r{self.desc}: [{bar}] {percent}% {status} {eta_str}", end='', flush=True)
        self._displayed = True
    
    def close(self):
        """Закрытие индикатора прогресса"""
        if self._displayed:
            print()  # Новая строка после завершения


def create_progress_bar(total: int, desc: str = "", use_tqdm: bool = True):
    """Создание индикатора прогресса (tqdm или простой)"""
    if use_tqdm and TQDM_AVAILABLE:
        return tqdm(total=total, desc=desc, unit="", ncols=80, bar_format='{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]')
    else:
        return SimpleProgressBar(total, desc)


def format_time(seconds: float) -> str:
    """Форматирование времени для вывода"""
    if seconds < 0.001:
        return f"{seconds * 1_000_000:.2f} мкс"
    elif seconds < 1:
        return f"{seconds * 1000:.2f} мс"
    else:
        return f"{seconds:.2f} с"


def test_streebog(test_data: List[bytes], iterations: int = 10, verbose: bool = False, show_progress: bool = False) -> Dict:
    """Тестирование алгоритма Стрибог-512"""
    print("\n" + "="*60)
    print("ТЕСТ: Стрибог-512 (ГОСТ 34.11-2018)")
    print("="*60)
    
    results = []
    
    for i, data in enumerate(test_data, 1):
        print(f"\nТест {i}: Данные размером {len(data)} байт")
        
        if verbose:
            print("  [Этап 1] Инициализация:")
            print("    - h = 0^512 (начальный хеш)")
            print("    - n = 0 (счетчик обработанных бит)")
            print("    - sigma = 0 (сумма всех блоков)")
            blocks_count = (len(data) + 63) // 64
            full_blocks = len(data) // 64
            print(f"  [Этап 2] Анализ данных:")
            print(f"    - Размер данных: {len(data)} байт ({len(data) * 8} бит)")
            print(f"    - Полных блоков по 512 бит: {full_blocks}")
            print(f"    - Остаток: {len(data) % 64} байт")
        
        # Процесс хеширования
        times = []
        full_blocks = len(data) // 64
        total_steps = full_blocks + (2 if len(data) % 64 != 0 or len(data) < 64 else 0) + 2  # Полные блоки + последний блок + финальные шаги
        
        for iter_num in range(iterations):
            if verbose and iter_num == 0:
                print(f"  [Итерация {iter_num + 1}] Начало хеширования...")
                if full_blocks > 0:
                    print(f"    [Этап 2.1] Обработка {full_blocks} полных блоков по 512 бит...")
                    for block_num in range(full_blocks):
                        print(f"      [Блок {block_num + 1}] Применение функции gn(h, m, n)")
                if len(data) % 64 != 0 or len(data) < 64:
                    print(f"    [Этап 3.1] Обработка последнего неполного блока...")
                    print(f"      [Шаг 1] Дополнение блока единичным битом")
                    print(f"      [Шаг 2] Применение функции gn(h, m, n)")
                print(f"    [Этап 3.2] Обновление счетчика обработанных бит")
                print(f"    [Этап 3.3] Обновление суммы блоков")
                print(f"    [Этап 3.4] Финальное преобразование: gn(h, n, 0)")
                print(f"    [Этап 3.5] Финальное преобразование: gn(h, sigma, 0)")
            
            # Индикатор прогресса для итераций
            if show_progress and iter_num == 0:
                pbar = create_progress_bar(iterations, f"  Итерации хеширования", use_tqdm=not verbose)
            
            start = time.perf_counter()
            hash_result = streebog_512(data)
            end = time.perf_counter()
            times.append(end - start)
            
            if show_progress:
                if iter_num == 0:
                    pbar.update(1)
                else:
                    pbar.update(1)
                if iter_num == iterations - 1:
                    pbar.close()
            
            if verbose and iter_num == 0:
                print(f"  [Итерация {iter_num + 1}] Хеширование завершено за {format_time(end - start)}")
        
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        hash_hex = hash_result.hex()[:32] + "..."
        
        if verbose:
            print(f"  [Результат] Хеш вычислен: {hash_hex}")
        
        print(f"  Хеш (первые 32 символа): {hash_hex}")
        print(f"  Среднее время: {format_time(avg_time)}")
        print(f"  Минимальное: {format_time(min_time)}")
        print(f"  Максимальное: {format_time(max_time)}")
        print(f"  Скорость: {len(data) / avg_time / 1024 / 1024:.2f} МБ/с")
        
        results.append({
            'data_size': len(data),
            'avg_time': avg_time,
            'min_time': min_time,
            'max_time': max_time,
            'hash': hash_result.hex()
        })
    
    return {'algorithm': 'Стрибог-512', 'results': results}


def test_kuznechik(test_data: List[bytes], iterations: int = 10, verbose: bool = False, show_progress: bool = False) -> Dict:
    """Тестирование алгоритма Кузнечик"""
    print("\n" + "="*60)
    print("ТЕСТ: Кузнечик (ГОСТ Р 34.12-2018)")
    print("="*60)
    print("⚠️  Кузнечик работает только с блоками 16 байт (128 бит)")
    
    results = []
    
    # Генерация ключа
    print("\nГенерация ключа...")
    key_gen_times = []

    # Индикатор прогресса для генерации ключей
    if show_progress:
        pbar_keys = create_progress_bar(iterations, "  Генерация ключей", use_tqdm=not verbose)
    
    for iter_num in range(iterations):
        if verbose:
            print(f"  [Итерация {iter_num + 1}] Генерация ключа...")
            print(f"    [Шаг 1] Генерация итерационных констант C_i (32 константы)")
            print(f"    [Шаг 2] Генерация случайного ключа 256 бит")
            print(f"    [Шаг 3] Разделение ключа на K1 и K2")
            print(f"    [Шаг 4] Генерация 10 итерационных ключей через F функции")
        
        start = time.perf_counter()
        kuz = Kuznechik()
        end = time.perf_counter()
        key_gen_times.append(end - start)
        
        if show_progress:
            pbar_keys.update(1)
        
        if verbose:
            print(f"    [Готово] Ключ сгенерирован за {format_time(end - start)}")
    
    if show_progress:
        pbar_keys.close()
    
    avg_key_gen = sum(key_gen_times) / len(key_gen_times)
    print(f"  Среднее время генерации ключа: {format_time(avg_key_gen)}")
    
    # Использование одного ключа для всех тестов
    if verbose:
        print("\n  [Используем один ключ для всех тестов]")
    kuz = Kuznechik()

    for i, data in enumerate(test_data, 1):
        # Алгоритм Кузнечик работает только с блоками размером 16 байт
        if len(data) != 16:
            # Обрезаем до 16 байт или дополняем нулями до 16 байт
            test_block = data[:16] if len(data) >= 16 else data + b'\x00' * (16 - len(data))
            print(f"\nТест {i}: Данные размером {len(data)} байт → используем блок 16 байт")
        else:
            test_block = data
            print(f"\nТест {i}: Данные размером {len(data)} байт")
        
        # Процесс шифрования
        encrypt_times = []
        decrypt_times = []

        # Индикатор прогресса для шифрования и расшифрования
        if show_progress:
            pbar_crypto = create_progress_bar(iterations * 2, f"  Шифрование/расшифрование (тест {i})", use_tqdm=not verbose)
        
        for iter_num in range(iterations):
            if verbose and iter_num == 0:
                print(f"  [Итерация {iter_num + 1}] Шифрование блока...")
                print(f"    [Шаг 1] Преобразование блока в список байт")
                print(f"    [Шаг 2] 9 раундов LSX преобразований")
                print(f"    [Шаг 3] Финальное X преобразование")
            
            # Шифрование
            start = time.perf_counter()
            encrypted = kuz.encrypt(test_block)
            end = time.perf_counter()
            encrypt_times.append(end - start)
            
            if show_progress:
                pbar_crypto.update(1)
            
            if verbose and iter_num == 0:
                print(f"    [Готово] Блок зашифрован за {format_time(end - start)}")
                print(f"  [Итерация {iter_num + 1}] Расшифрование блока...")
                print(f"    [Шаг 1] Преобразование зашифрованного блока")
                print(f"    [Шаг 2] 9 раундов S_inv L_inv X преобразований")
                print(f"    [Шаг 3] Финальное X преобразование")
            
            # Расшифрование
            start = time.perf_counter()
            decrypted = kuz.decrypt(encrypted)
            end = time.perf_counter()
            decrypt_times.append(end - start)
            
            if show_progress:
                pbar_crypto.update(1)
            
            if verbose and iter_num == 0:
                print(f"    [Готово] Блок расшифрован за {format_time(end - start)}")
            
            # Проверка корректности
            if decrypted != test_block:
                print(f"  ⚠️  ОШИБКА: Расшифрованные данные не совпадают!")
            elif verbose and iter_num == 0:
                print(f"    [Проверка] ✓ Расшифрованные данные совпадают с исходными")
        
        if show_progress:
            pbar_crypto.close()
        
        avg_encrypt = sum(encrypt_times) / len(encrypt_times)
        avg_decrypt = sum(decrypt_times) / len(decrypt_times)
        
        print(f"  Шифрование - среднее: {format_time(avg_encrypt)}")
        print(f"  Расшифрование - среднее: {format_time(avg_decrypt)}")
        print(f"  Скорость шифрования: {len(test_block) / avg_encrypt / 1024 / 1024:.2f} МБ/с")
        print(f"  Скорость расшифрования: {len(test_block) / avg_decrypt / 1024 / 1024:.2f} МБ/с")
        
        results.append({
            'data_size': len(test_block),
            'key_gen_time': avg_key_gen,
            'encrypt_time': avg_encrypt,
            'decrypt_time': avg_decrypt
        })
    
    return {'algorithm': 'Кузнечик', 'results': results}


# Блокировка для синхронизации вывода при параллельном выполнении
_output_lock = threading.Lock()
# Словарь для хранения позиций строк при параллельной генерации
_line_positions = {'p': 0, 'q': 1}

def generate_prime_with_logging(bits: int, name: str, show_progress: bool, verbose: bool, parallel: bool):
    """Генерация простого числа с подробным логированием для использования в потоках"""
    import gmpy2
    from gmpy2 import mpz

    attempts = 0
    start_time = time.time()
    last_output_time = start_time
    pbar = None
    line_pos = _line_positions.get(name, 0)

    if show_progress:
        pbar = create_progress_bar(None, f"    Поиск простого числа {name}", use_tqdm=not verbose)
    
    while True:
        attempts += 1
        current_time = time.time()
        elapsed = current_time - start_time
        time_since_last_output = current_time - last_output_time
        
        should_output = False
        # Первая попытка всегда выводится, если не используется индикатор прогресса
        first_attempt = (attempts == 1) and not show_progress

        if verbose:
            # В режиме подробного вывода: каждые 10 секунд или каждые 100 попыток или первая попытка
            should_output = (time_since_last_output >= 10.0) or (attempts % 100 == 0) or first_attempt
        elif not show_progress:
            # В обычном режиме без индикатора прогресса: каждые 10 секунд или каждые 1000 попыток или первая попытка
            should_output = (time_since_last_output >= 10.0) or (attempts % 1000 == 0) or first_attempt
        # Если включен индикатор прогресса, вывод логов не требуется
        
        if should_output:
            with _output_lock:  # Синхронизация вывода при параллельном выполнении
                if verbose:
                    print(f"    [{name}] Попытка {attempts}... (прошло {elapsed:.1f}с)")
                elif not show_progress:  # Обычный режим без индикатора прогресса
                    if parallel:
                        # В режиме параллельной генерации выводим обновления в отдельных строках с блокировкой
                        # Блокировка предотвращает смешивание строк от разных потоков
                        print(f"    [{name}] Попытка {attempts}... (прошло {elapsed:.1f}с)")
                    else:
                        # Последовательный режим - перезапись текущей строки
                        print(f"\r    Поиск простого числа {name}: попытка {attempts}... (прошло {elapsed:.1f}с)", end='', flush=True)
            last_output_time = current_time
        
        if show_progress and pbar:
            pbar.current = attempts
            pbar._display()
        
        candidate = gmpy2.mpz_random(gmpy2.random_state(), mpz(2) ** bits)
        candidate |= mpz(1) << (bits - 1)
        
        if gmpy2.is_prime(candidate):
            with _output_lock:  # Синхронизация финального вывода
                if show_progress and pbar:
                    pbar.current = attempts
                    pbar.total = attempts
                    pbar._display()
                    pbar.close()
                if not show_progress and not verbose:
                    if not parallel:
                        print()  # Новая строка после однострочного вывода в последовательном режиме
                elapsed_total = time.time() - start_time
                # Вывод финального сообщения о нахождении простого числа
                if not show_progress:
                    print(f"    ✓ Простое число {name} найдено за {attempts} попыток ({elapsed_total:.1f}с)")
                elif verbose:
                    print(f"    ✓ Простое число {name} найдено за {attempts} попыток ({elapsed_total:.1f}с)")
            return candidate, attempts, elapsed_total


def test_rsa(test_data: List[bytes], iterations: int = 5, verbose: bool = False, show_progress: bool = False, parallel: bool = True) -> Dict:
    """Тестирование алгоритма RSA-32768"""
    print("\n" + "="*60)
    print("ТЕСТ: RSA-32768")
    print("="*60)
    print("⚠️  ВНИМАНИЕ: Генерация ключей RSA-32768 может занять много времени!")
    
    results = []

    # Генерация ключей выполняется один раз из-за высокой вычислительной сложности
    print("\nГенерация ключей RSA-32768...")
    print("Это может занять несколько минут...")
    print("\nПояснение: RSA-32768 означает, что модуль n имеет длину 32768 бит.")
    print("Модуль вычисляется как n = p × q, где p и q - простые числа.")
    print("Для получения n длиной 32768 бит каждое простое должно быть ~16384 бит (32768 / 2 = 16384).")
    print("\nТеория сложности:")
    print("  • Вероятность простого числа ~16384 бит: ≈ 1/11,356 (теорема о распределении простых)")
    print("  • Ожидаемое количество попыток: ~11,356 попыток на одно простое число")
    print("  • Время проверки на простоту: ~5-60 секунд на проверку (для чисел такого размера)")
    print("  • Общее время: ~5-60 минут на генерацию пары ключей")
    print("\nПричины высокой сложности:")
    print("  1. Низкая плотность простых чисел в диапазоне")
    print("  2. Каждая проверка на простоту требует миллионов операций")
    print("  3. Операции выполняются с числами длиной ~2000 байт")
    print("  4. Это цена безопасности RSA")

    # Режим параллельной генерации включен по умолчанию
    if parallel:
        print("\nРежим параллельной генерации: p и q генерируются одновременно (ускорение ~2x)")
    else:
        print("\nПоследовательный режим: p и q генерируются по очереди (медленнее)")
    print()
    
    start = time.perf_counter()
    import gmpy2
    from gmpy2 import mpz
    
    if parallel:
        # Параллельная генерация простых чисел p и q
        print("  [Параллельная генерация] Запуск генерации p и q одновременно...")
        print()

        with ThreadPoolExecutor(max_workers=2) as executor:
            # Запуск обоих потоков одновременно
            future_p = executor.submit(generate_prime_with_logging, 16384, "p", show_progress, verbose, parallel)
            future_q = executor.submit(generate_prime_with_logging, 16384, "q", show_progress, verbose, parallel)

            # Ожидание завершения обоих потоков
            p, p_attempts, p_time = future_p.result()
            q, q_attempts, q_time = future_q.result()

        total_time = max(p_time, q_time)  # Общее время определяется самым долгим потоком
        print(f"\n  Параллельная генерация завершена")
        print(f"    p: {p_attempts} попыток ({p_time:.1f}с)")
        print(f"    q: {q_attempts} попыток ({q_time:.1f}с)")
        print(f"    Общее время: {total_time:.1f}с (вместо {p_time + q_time:.1f}с последовательно)")
        print(f"    Ускорение: {((p_time + q_time) / total_time):.2f}x")
    else:
        # Последовательная генерация простых чисел
        print("  [Этап 1] Генерация первого простого числа p (16384 бит)...")
        p, p_attempts, p_time = generate_prime_with_logging(16384, "p", show_progress, verbose, parallel)

        print(f"\n  [Этап 2] Генерация второго простого числа q (16384 бит)...")
        q, q_attempts, q_time = generate_prime_with_logging(16384, "q", show_progress, verbose, parallel)

        total_time = p_time + q_time
    
    print(f"  [Этап 3] Вычисление n = p * q...")
    n = p * q
    print(f"  [Этап 4] Вычисление phi(n) = (p-1) * (q-1)...")
    phi_n = (p - 1) * (q - 1)
    print(f"  [Этап 5] Выбор открытой экспоненты e = 65537...")
    e = mpz(65537)
    print(f"  [Этап 6] Вычисление секретной экспоненты d = e^(-1) mod phi(n)...")
    d = gmpy2.invert(e, phi_n)
    print(f"  ✓ Все ключи сгенерированы")
    rsa = RSA32768(p=p, q=q, n=n, e=e, d=d)
    
    key_gen_time = time.perf_counter() - start
    print(f"  Время генерации ключей: {format_time(key_gen_time)}")
    
    for i, data in enumerate(test_data, 1):
        # RSA-32768 имеет ограничение на размер шифруемых данных
        max_size = 4094  # Максимальный размер для RSA-32768 с дополнением
        if len(data) > max_size:
            print(f"\nТест {i}: Данные размером {len(data)} байт - ПРОПУЩЕН")
            print(f"  RSA-32768 может шифровать максимум {max_size} байт")
            continue
        
        print(f"\nТест {i}: Данные размером {len(data)} байт")

        # Процесс шифрования и расшифрования
        encrypt_times = []
        decrypt_times = []

        # Индикатор прогресса для шифрования и расшифрования
        if show_progress:
            pbar_rsa = create_progress_bar(iterations * 2, f"  Шифрование/расшифрование RSA (тест {i})", use_tqdm=not verbose)
        
        for iter_num in range(iterations):
            if verbose and iter_num == 0:
                print(f"  [Итерация {iter_num + 1}] Шифрование данных...")
                print(f"    [Шаг 1] Дополнение сообщения до 4096 байт")
                print(f"    [Шаг 2] Преобразование в большое число (big-endian)")
                print(f"    [Шаг 3] Вычисление c = m^e mod n (быстрое возведение в степень)")
            
            # Шифрование
            start = time.perf_counter()
            encrypted = rsa.encrypt(data)
            end = time.perf_counter()
            encrypt_times.append(end - start)
            
            if show_progress:
                pbar_rsa.update(1)
            
            if verbose and iter_num == 0:
                print(f"    [Готово] Данные зашифрованы за {format_time(end - start)}")
                print(f"  [Итерация {iter_num + 1}] Расшифрование данных...")
                print(f"    [Шаг 1] Преобразование зашифрованных данных в число")
                print(f"    [Шаг 2] Вычисление m = c^d mod n (быстрое возведение в степень)")
                print(f"    [Шаг 3] Удаление дополнения и извлечение исходного сообщения")
            
            # Расшифрование
            start = time.perf_counter()
            decrypted = rsa.decrypt(encrypted)
            end = time.perf_counter()
            decrypt_times.append(end - start)
            
            if show_progress:
                pbar_rsa.update(1)
            
            if verbose and iter_num == 0:
                print(f"    [Готово] Данные расшифрованы за {format_time(end - start)}")
            
            # Проверка корректности
            if decrypted != data:
                print(f"  ⚠️  ОШИБКА: Расшифрованные данные не совпадают!")
            elif verbose and iter_num == 0:
                print(f"    [Проверка] ✓ Расшифрованные данные совпадают с исходными")
        
        if show_progress:
            pbar_rsa.close()
        
        avg_encrypt = sum(encrypt_times) / len(encrypt_times)
        avg_decrypt = sum(decrypt_times) / len(decrypt_times)
        
        print(f"  Шифрование - среднее: {format_time(avg_encrypt)}")
        print(f"  Расшифрование - среднее: {format_time(avg_decrypt)}")
        print(f"  Скорость шифрования: {len(data) / avg_encrypt / 1024:.2f} КБ/с")
        print(f"  Скорость расшифрования: {len(data) / avg_decrypt / 1024:.2f} КБ/с")
        
        results.append({
            'data_size': len(data),
            'key_gen_time': key_gen_time,
            'encrypt_time': avg_encrypt,
            'decrypt_time': avg_decrypt
        })
    
    return {'algorithm': 'RSA-32768', 'results': results}


def main():
    parser = argparse.ArgumentParser(
        description='Тестирование криптографических алгоритмов с замером времени',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python test_algorithms.py --all
  python test_algorithms.py --streebog --iterations 20
  python test_algorithms.py --kuznechik --data-size 1024
  python test_algorithms.py --rsa --iterations 3
  python test_algorithms.py --all --verbose  # Подробное логирование
  python test_algorithms.py --all --progress  # Индикаторы прогресса с процентами
  python test_algorithms.py --all --verbose --progress  # Подробное логирование с индикаторами прогресса
  python test_algorithms.py --rsa  # Параллельная генерация p и q включена по умолчанию (ускорение ~2x)
  python test_algorithms.py --rsa --no-parallel  # Отключить параллельную генерацию
        """
    )
    
    parser.add_argument('--all', action='store_true', help='Тестировать все алгоритмы')
    parser.add_argument('--streebog', action='store_true', help='Тестировать Стрибог-512')
    parser.add_argument('--kuznechik', action='store_true', help='Тестировать Кузнечик')
    parser.add_argument('--rsa', action='store_true', help='Тестировать RSA-32768')
    parser.add_argument('--iterations', type=int, default=10, help='Количество итераций для каждого теста (по умолчанию: 10)')
    parser.add_argument('--data-size', type=int, nargs='+', default=[16, 64, 256, 1024, 4096], 
                       help='Размеры тестовых данных в байтах (по умолчанию: 16 64 256 1024 4096)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Подробное логирование этапов работы алгоритмов')
    parser.add_argument('--progress', '-p', action='store_true', help='Показывать индикаторы прогресса с процентами')
    parser.add_argument('--no-parallel', dest='parallel', action='store_false', default=True, help='Отключить параллельную генерацию (последовательная генерация). По умолчанию параллелизация включена')
    
    args = parser.parse_args()
    
    # Если не выбран конкретный алгоритм, тестируются все
    if not any([args.all, args.streebog, args.kuznechik, args.rsa]):
        args.all = True

    # Подготовка тестовых данных
    # Для алгоритма Кузнечик требуются блоки размером 16 байт
    test_data = [os.urandom(size) for size in args.data_size]
    # Добавление блока 16 байт для Кузнечика, если он отсутствует в списке
    if 16 not in args.data_size:
        test_data.insert(0, os.urandom(16))
    
    print("="*60)
    print("ТЕСТИРОВАНИЕ КРИПТОГРАФИЧЕСКИХ АЛГОРИТМОВ")
    print("="*60)
    print(f"Количество итераций: {args.iterations}")
    print(f"Размеры тестовых данных: {args.data_size} байт")
    
    results = []
    
    # Тестирование Стрибог
    if args.all or args.streebog:
        try:
            result = test_streebog(test_data, args.iterations, args.verbose, args.progress)
            results.append(result)
        except Exception as e:
            print(f"\n❌ ОШИБКА при тестировании Стрибог: {e}")
    
    # Тестирование Кузнечик
    if args.all or args.kuznechik:
        try:
            result = test_kuznechik(test_data, args.iterations, args.verbose, args.progress)
            results.append(result)
        except Exception as e:
            print(f"\n❌ ОШИБКА при тестировании Кузнечик: {e}")
    
    # Тестирование RSA
    if args.all or args.rsa:
        if not RSA_AVAILABLE:
            print("\nRSA-32768 пропущен: gmpy2 не установлен")
            print("   Установите: pip install gmpy2")
        else:
            try:
                # Для RSA используется меньше итераций из-за высокой вычислительной сложности
                rsa_iterations = min(args.iterations, 5)
                # Параллельная генерация включена по умолчанию
                # Если пользователь не указал флаг --no-parallel, используется параллельный режим
                parallel_mode = getattr(args, 'parallel', True)
                if not hasattr(args, 'parallel'):
                    parallel_mode = True  # Параллельный режим по умолчанию
                result = test_rsa(test_data, rsa_iterations, args.verbose, args.progress, parallel_mode)
                results.append(result)
            except Exception as e:
                print(f"\nОшибка при тестировании RSA-32768: {e}")
    
    # Итоговая сводка
    print("\n" + "="*60)
    print("ИТОГОВАЯ СВОДКА")
    print("="*60)
    
    for result in results:
        print(f"\n{result['algorithm']}:")
        for r in result['results']:
            if 'avg_time' in r:
                print(f"  {r['data_size']} байт: {format_time(r['avg_time'])}")
            elif 'encrypt_time' in r:
                print(f"  {r['data_size']} байт: шифр={format_time(r['encrypt_time'])}, расшифр={format_time(r['decrypt_time'])}")
    
    print("\n" + "="*60)
    print("Тестирование завершено!")
    print("="*60)


if __name__ == '__main__':
    main()

