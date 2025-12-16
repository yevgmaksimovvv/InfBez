"""
Реализация RSA-32768 с использованием GMP
Генерация простых чисел на основе GMP
Асимметричный алгоритм шифрования с длиной ключа 32768 бит
"""
import gmpy2
from gmpy2 import mpz
from typing import Tuple, Optional
import os


class RSA32768:
    """
    RSA с ключами длиной 32768 бит
    """
    
    def __init__(self, p: Optional[mpz] = None, q: Optional[mpz] = None, 
                 n: Optional[mpz] = None, e: Optional[mpz] = None, d: Optional[mpz] = None):
        """
        Инициализация с ключами или генерация новых
        """
        if all(x is not None for x in [p, q, n, e, d]):
            self.p = p
            self.q = q
            self.n = n
            self.public_key = e
            self.private_key = d
        else:
            keys = self.generate_keys()
            self.p = keys['p']
            self.q = keys['q']
            self.n = keys['n']
            self.public_key = keys['e']
            self.private_key = keys['d']
    
    @staticmethod
    def generate_prime(bits: int) -> mpz:
        """
        Генерация простого числа заданной длины в битах
        Использует библиотеку GMP для эффективной генерации
        """
        # Генерация случайного числа нужной длины
        while True:
            # Генерация случайного числа
            candidate = gmpy2.mpz_random(gmpy2.random_state(), mpz(2) ** bits)
            # Установка старшего бита для обеспечения нужной длины
            candidate |= mpz(1) << (bits - 1)
            # Проверка числа на простоту
            if gmpy2.is_prime(candidate):
                return candidate
    
    @staticmethod
    def coprime(a: mpz, b: mpz) -> bool:
        """
        Проверка взаимной простоты двух чисел с использованием алгоритма Евклида
        """
        while b != 0:
            a, b = b, a % b
        return a == 1
    
    @staticmethod
    def modpow(base: mpz, exp: mpz, modulus: mpz) -> mpz:
        """
        Быстрое возведение в степень по модулю
        Использует оптимизированную функцию gmpy2.powmod
        """
        return gmpy2.powmod(base, exp, modulus)
    
    def generate_keys(self) -> dict:
        """
        Генерация пары ключей длиной 32768 бит
        """
        # Генерация двух различных простых чисел по 16384 бит каждое
        # Требование: p и q должны быть различными простыми числами
        # Различные простые числа автоматически взаимно просты
        p = self.generate_prime(16384)
        q = self.generate_prime(16384)

        # Проверка неравенства p и q (вероятность совпадения пренебрежимо мала)
        # Это условие критично для корректности алгоритма RSA
        while p == q:
            q = self.generate_prime(16384)

        # Вычисление модуля n = p * q
        n = p * q

        # Вычисление функции Эйлера phi(n) = (p-1) * (q-1)
        phi_n = (p - 1) * (q - 1)

        # Выбор открытой экспоненты (стандартное значение 65537)
        e = mpz(65537)

        # Проверка взаимной простоты e и phi(n)
        if not self.coprime(e, phi_n):
            # Генерация альтернативного малого простого числа
            e = self.generate_prime(16)

        # Вычисление секретной экспоненты d = e^(-1) mod phi(n)
        d = gmpy2.invert(e, phi_n)
        
        return {
            'p': p,
            'q': q,
            'n': n,
            'e': e,
            'd': d
        }
    
    def encrypt(self, message: bytes) -> bytes:
        """
        Шифрование сообщения с применением дополнения

        Схема дополнения:
        - Первые 2 байта содержат нули для обеспечения условия m < N
        - Байты 2-3 содержат длину дополнения
        - Исходное сообщение размещается в конце блока

        Args:
            message: Сообщение для шифрования (максимальная длина 4094 байта)

        Returns:
            Зашифрованное сообщение фиксированной длины 4096 байт
        """
        if len(message) >= 4096:
            raise ValueError("Message too long for RSA-32768 encryption")

        buf = bytearray(4096)
        pad_len = 4096 - len(message)

        # Запись длины дополнения в байты 2-3
        buf[2] = (pad_len // 256) & 0xFF
        buf[3] = pad_len % 256

        # Размещение сообщения в конце буфера
        buf[pad_len:] = message

        # Преобразование в число (порядок байтов big-endian)
        m = mpz(int.from_bytes(buf, byteorder='big'))

        if m >= self.n:
            raise ValueError("Message too large for modulus")

        # Шифрование: c = m^e mod n
        cipher_text = self.modpow(m, self.public_key, self.n)

        # Преобразование результата обратно в байты
        return cipher_text.to_bytes(4096, byteorder='big')
    
    def decrypt(self, cipher_text: bytes) -> bytes:
        """
        Расшифрование сообщения с удалением дополнения

        Извлекает исходное сообщение из зашифрованных данных

        Args:
            cipher_text: Зашифрованное сообщение фиксированной длины 4096 байт

        Returns:
            Расшифрованное исходное сообщение
        """
        if len(cipher_text) != 4096:
            raise ValueError("Cipher text must be 4096 bytes")

        # Преобразование байтов в число
        c = mpz(int.from_bytes(cipher_text, byteorder='big'))

        # Расшифрование: m = c^d mod n
        text = self.modpow(c, self.private_key, self.n)

        # Преобразование результата обратно в байты
        text_b = text.to_bytes(4096, byteorder='big')

        # Извлечение длины дополнения из байтов 2-3
        pad_len = (text_b[2] * 256) + text_b[3]

        # Возврат исходного сообщения без дополнения
        return text_b[4096 - pad_len:]

