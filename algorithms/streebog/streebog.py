"""
Реализация алгоритма Стрибог (ГОСТ 34.11-2018)
Криптографический алгоритм вычисления хеш-функции
Размер блока входных данных: 512 бит
Размер хеш-кода: 512 бит
"""
import struct
from .consts import A, P, T, C


def sum_mod2(str1: bytes, str2: bytes) -> bytes:
    """
    Суммирование по модулю 2 (XOR)
    """
    if len(str1) != len(str2):
        raise ValueError("Str1 and str2 length not equal")
    
    return bytes(a ^ b for a, b in zip(str1, str2))


def sum_mod2_wo(left: bytes, right: bytes) -> bytes:
    """
    Суммирование в кольце Z_2^N (с переносом)
    """
    if len(left) != len(right):
        raise ValueError("Left and right length not equal")
    
    result = bytearray(len(left))
    carry = 0
    
    for idx in range(len(left)):
        res = left[idx] + right[idx] + carry
        result[idx] = res & 0xFF  # Обрезает старшие биты
        carry = res >> 8  # Оставляет старшие биты (бит переноса)
    
    return bytes(result)


def power_to_u64(rem: int) -> bytes:
    """
    Получить мощность сообщения в формате [u8; 64]
    """
    m_power = bytearray(64)
    rem_b = rem.to_bytes(8, byteorder='little')
    m_power[:len(rem_b)] = rem_b
    return bytes(m_power)


def mul_matrice(b: bytes) -> bytes:
    """
    Умножение с матрицей A
    """
    if len(b) != 8:
        raise ValueError("b must be 8 bytes")
    
    out = bytearray(8)
    
    for n_byte, byte_val in enumerate(b):
        cur_bit = 1
        for n_bit in range(8):
            if (byte_val & cur_bit) != 0:
                row_u64 = A[63 - (n_byte * 8 + n_bit)]
                row_bytes = struct.pack('<Q', row_u64)  # little-endian u64
                out = bytearray(sum_mod2(bytes(out), row_bytes))
            
            cur_bit <<= 1
    
    return bytes(out)


def lps(v: bytes) -> bytes:
    """
    Последовательность операций, выполняемых в порядке: s, p, l
    """
    if len(v) != 64:
        raise ValueError("v must be 64 bytes")
    
    res = bytearray(64)
    
    # S - нелинейное преобразование
    for index in range(64):
        res[index] = P[v[index]]
    
    src = res.copy()
    
    # P - перестановка байт
    for index in range(64):
        res[index] = src[T[index]]
    
    # L - линейное преобразование
    for index in range(8):
        offset = 8 * index
        slice_bytes = res[offset:offset + 8]
        res[offset:offset + 8] = mul_matrice(bytes(slice_bytes))
    
    return bytes(res)


def gn(h: bytes, m: bytes, n: bytes) -> bytes:
    """
    Функция сжатия
    """
    if len(h) != 64 or len(m) != 64 or len(n) != 64:
        raise ValueError("h, m, n must be 64 bytes")
    
    # K_1 = LPS(h sum_mod2 N)
    k = lps(sum_mod2(h, n))
    
    # Для первого действия LPS(K1 sum_mod2 M)
    x = bytearray(m)
    
    # Е(К, m) = X[K_13]LPSX[K_12]...LPSX[K_1](m).
    for n_iter in range(12):
        x = bytearray(lps(sum_mod2(k, bytes(x))))
        
        # K_(i+1) = LPS(K_i sum_mod2 C_i)
        k = lps(sum_mod2(k, bytes(C[n_iter])))
    
    x = bytearray(sum_mod2(k, bytes(x)))  # X[K_13]
    x = bytearray(sum_mod2(bytes(x), h))  # E mod_sum2 h
    x = bytearray(sum_mod2(bytes(x), m))  # E mod_sum2 h mod_sum2 m
    
    return bytes(x)


def streebog_512(message: bytes) -> bytes:
    """
    Хэширование алгоритмом Стрибог-512 (ГОСТ 34.11-2018)
    
    Вычисляет хеш-код для сообщения произвольной длины.
    Размер блока входных данных: 512 бит
    Размер хеш-кода: 512 бит (64 байта)
    
    Args:
        message: Входное сообщение в виде байтов
        
    Returns:
        Хеш-код длиной 64 байта (512 бит)
    """
    # Этап 1: Присваивание начальных значений
    # Для 512 бит: h = 0^512
    h = bytes(64)
    
    n = bytes(64)  # Счетчик обработанных бит
    sigma = bytes(64)  # Сумма всех блоков сообщения
    m = bytearray(64)  # Текущий блок сообщения
    
    count512 = 0  # Счетчик полных блоков по 512 бит
    
    # Этап 2: Обработка полных блоков по 512 бит
    while (len(message) - count512 * 64) * 8 >= 512:
        # Значение 512 в формате 64 байта (little-endian)
        t512 = bytearray(64)
        t512[1] = 2
        
        # Получение подвектора длины 512 бит
        m = bytearray(message[count512 * 64:count512 * 64 + 64])
        
        h = gn(h, bytes(m), n)  # h := gn(h, m)
        n = sum_mod2_wo(n, bytes(t512))  # N := Vec512(lnt512(N) sum_mod2 512)
        sigma = sum_mod2_wo(sigma, bytes(m))  # sigma := Vec512(lnt512(sigma) sum_mod2 Int512(m))
        
        count512 += 1
    
    # Этап 3: Обработка последнего неполного блока
    # Дополнение последнего блока
    m = bytearray(64)
    remaining = message[count512 * 64:]
    m[:len(remaining)] = remaining
    m[len(remaining)] = 1  # Добавление единичного бита
    
    h = gn(h, bytes(m), n)  # h := gn(h, m)
    
    # Мощность сообщения M в битах
    m_len = 8 * (len(message) - count512 * 64)
    
    # Обновление счетчика обработанных бит
    n = sum_mod2_wo(n, power_to_u64(m_len))
    
    # Обновление суммы блоков
    sigma = sum_mod2_wo(sigma, bytes(m))
    
    # Финальное преобразование
    h = gn(h, n, bytes(64))  # h := g0(h, N)
    h = gn(h, sigma, bytes(64))  # Финальный хеш
    
    # Возврат хеш-кода (512 бит = 64 байта)
    return h

