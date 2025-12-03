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
        Генерация простого числа длиной bits бит
        Использует GMP для генерации
        """
        # Генерируем случайное число нужной длины
        while True:
            # Генерируем случайное число
            candidate = gmpy2.mpz_random(gmpy2.random_state(), mpz(2) ** bits)
            # Устанавливаем старший бит для нужной длины
            candidate |= mpz(1) << (bits - 1)
            # Проверяем на простоту
            if gmpy2.is_prime(candidate):
                return candidate
    
    @staticmethod
    def coprime(a: mpz, b: mpz) -> bool:
        """
        Проверка взаимной простоты (алгоритм Евклида)
        """
        while b != 0:
            a, b = b, a % b
        return a == 1
    
    @staticmethod
    def modpow(base: mpz, exp: mpz, modulus: mpz) -> mpz:
        """
        Быстрое возведение в степень по модулю
        """
        if modulus == 1:
            return mpz(0)
        
        result = mpz(1)
        base = base % modulus
        
        while exp > 0:
            if exp % 2 == 1:
                result = (result * base) % modulus
            exp = exp >> 1
            base = (base * base) % modulus
        
        return result
    
    def generate_keys(self) -> dict:
        """
        Генерация ключей длиной 32768 бит
        """
        # Генерируем два простых числа по 16384 бит каждое
        # Важно: p и q должны быть разными простыми числами
        # Разные простые числа автоматически взаимно просты (НОД(p, q) = 1)
        p = self.generate_prime(16384)
        q = self.generate_prime(16384)
        
        # Проверяем, что p != q (на практике вероятность совпадения исчезающе мала)
        # но для корректности алгоритма RSA важно, чтобы они были разными
        while p == q:
            q = self.generate_prime(16384)
        
        # n = p * q
        n = p * q
        
        # phi(n) = (p-1) * (q-1)
        phi_n = (p - 1) * (q - 1)
        
        # Открытая экспонента (обычно 65537)
        e = mpz(65537)
        
        # Проверяем, что e и phi(n) взаимно просты
        if not self.coprime(e, phi_n):
            # Если нет, генерируем другое простое число
            e = self.generate_prime(16)  # Маленькое простое число
        
        # Вычисляем секретную экспоненту d = e^(-1) mod phi(n)
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
        Шифрование сообщения с дополнением
        
        Схема дополнения:
        - Старшие 2 байта нулевые, чтобы m < N
        - Байты 2-3 содержат длину дополнения
        - Сообщение размещается в конце блока
        
        Args:
            message: Сообщение для шифрования (максимум 4094 байта)
            
        Returns:
            Зашифрованное сообщение длиной 4096 байт
        """
        if len(message) >= 4096:
            raise ValueError("Message too long for RSA-32768 encryption")
        
        buf = bytearray(4096)
        pad_len = 4096 - len(message)
        
        # Записываем длину дополнения
        buf[2] = (pad_len // 256) & 0xFF
        buf[3] = pad_len % 256
        
        # Вставляем сообщение в конец
        buf[pad_len:] = message
        
        # Преобразуем в число (big-endian)
        m = mpz(int.from_bytes(buf, byteorder='big'))
        
        if m >= self.n:
            raise ValueError("Message too large for modulus")
        
        # Шифруем: c = m^e mod n
        cipher_text = self.modpow(m, self.public_key, self.n)
        
        # Преобразуем обратно в байты
        return cipher_text.to_bytes(4096, byteorder='big')
    
    def decrypt(self, cipher_text: bytes) -> bytes:
        """
        Расшифрование сообщения
        
        Удаляет дополнение и возвращает исходное сообщение
        
        Args:
            cipher_text: Зашифрованное сообщение длиной 4096 байт
            
        Returns:
            Расшифрованное сообщение
        """
        if len(cipher_text) != 4096:
            raise ValueError("Cipher text must be 4096 bytes")
        
        # Преобразуем в число
        c = mpz(int.from_bytes(cipher_text, byteorder='big'))
        
        # Расшифровываем: m = c^d mod n
        text = self.modpow(c, self.private_key, self.n)
        
        # Преобразуем обратно в байты
        text_b = text.to_bytes(4096, byteorder='big')
        
        # Извлекаем длину дополнения
        pad_len = (text_b[2] * 256) + text_b[3]
        
        # Возвращаем текст без дополнения
        return text_b[4096 - pad_len:]

