"""
Реализация алгоритма Кузнечик (ГОСТ Р 34.12-2018)
Блочный шифр с размером блока 128 бит и длиной ключа 256 бит
"""
import os
from typing import Tuple, List
from .consts import KUZ_PI, KUZ_PI_INV, L_VEC


class Kuznechik:
    """
    Алгоритм блочного шифрования Кузнечик
    Размер блока: 128 бит
    Размер ключа: 256 бит
    """
    
    def __init__(self, key: bytes = None):
        """
        Инициализация с ключом или генерация нового
        """
        if key is None:
            self.keys = self.key_generate()
        else:
            if len(key) != 32:
                raise ValueError(f"Key length must be 32 bytes, got {len(key)}")
            self.keys = self.key_generate_with_precomputed_key(key)
    
    @staticmethod
    def mul_gf2_px(elem1: int, elem2: int) -> int:
        """
        Конечное поле GF(2){x}/p(x), где р(х) = х^8 + х^7 + х^6 + х + 1
        Элементы поля F представляются целыми числами
        """
        px = 0b1100_0011  # х^8 + х^7 + х^6 + х + 1
        
        a = elem1
        b = elem2
        res = 0
        
        for _ in range(8):
            # Младший бит 1 - значит умножаем
            if b & 1 != 0:
                res ^= a
            
            carry = a & 0x80
            a = (a << 1) & 0xFF  # Сдвиг влево множимого
            
            if carry != 0:
                a ^= px  # XOR множимого, так как степень > 7
            
            b >>= 1  # Сдвиг множителя вправо
        
        return res
    
    @staticmethod
    def linear(a: List[int]) -> int:
        """
        Линейное преобразование
        Формула (1) страница 3 ГОСТ Р 34.12-2018
        """
        res = 0
        
        for idx, elem in enumerate(a):
            res ^= Kuznechik.mul_gf2_px(elem, L_VEC[idx])
        
        return res
    
    @staticmethod
    def x(k: List[int], a: List[int]) -> List[int]:
        """
        Формула (2) страница 4 ГОСТ Р 34.12-2018
        Операция XOR (суммирование по модулю 2)
        """
        return [k[i] ^ a[i] for i in range(16)]
    
    @staticmethod
    def s(a: List[int]) -> List[int]:
        """
        Формула (3) страница 4 ГОСТ Р 34.12-2018
        Нелинейное биективное преобразование
        """
        return [KUZ_PI[a[i]] for i in range(16)]
    
    @staticmethod
    def s_inv(a: List[int]) -> List[int]:
        """
        Формула (4) страница 4 ГОСТ Р 34.12-2018
        Обратное нелинейное биективное преобразование
        """
        return [KUZ_PI_INV[a[i]] for i in range(16)]
    
    @staticmethod
    def r(a: List[int]) -> List[int]:
        """
        Формула (5) страница 4 ГОСТ Р 34.12-2018
        Линейное преобразование с циклическим сдвигом
        """
        res = [0] * 16
        l_part = Kuznechik.linear(a)
        
        # l_part||а15, ..., а1
        res[15] = l_part
        res[:15] = a[1:]
        
        return res
    
    @staticmethod
    def r_inv(a: List[int]) -> List[int]:
        """
        Формула (7) страница 4 ГОСТ Р 34.12-2018
        Обратное линейное преобразование с циклическим сдвигом
        """
        res = [0] * 16
        # а14, а13, ..., а0, а15
        permutation = [a[15]] + a[:15]
        
        # (а14, а13, ..., а0, а15)
        l_part = Kuznechik.linear(permutation)
        
        # а14, ..., а0||l_part
        res[0] = l_part
        res[1:] = permutation[1:]
        
        return res
    
    @staticmethod
    def l(a: List[int]) -> List[int]:
        """
        Формула (6) страница 4 ГОСТ Р 34.12-2018
        Линейное преобразование (16 применений R)
        """
        res = a.copy()
        
        for _ in range(16):
            res = Kuznechik.r(res)
        
        return res
    
    @staticmethod
    def l_inv(a: List[int]) -> List[int]:
        """
        Формула (8) страница 4 ГОСТ Р 34.12-2018
        Обратное линейное преобразование (16 применений R_inv)
        """
        res = a.copy()
        
        for _ in range(16):
            res = Kuznechik.r_inv(res)
        
        return res
    
    @staticmethod
    def lsx(k: List[int], a: List[int]) -> List[int]:
        """
        Последовательность операций: X, S, L
        """
        res = Kuznechik.x(k, a)
        res = Kuznechik.s(res)
        res = Kuznechik.l(res)
        return res
    
    @staticmethod
    def s_inv_l_inv_x(k: List[int], a: List[int]) -> List[int]:
        """
        Последовательность операций: X, L_inv, S_inv
        """
        res = Kuznechik.x(k, a)
        res = Kuznechik.l_inv(res)
        res = Kuznechik.s_inv(res)
        return res
    
    @staticmethod
    def fk(k: List[int], a1: List[int], a0: List[int]) -> Tuple[List[int], List[int]]:
        """
        Формула (9) страница 4 ГОСТ Р 34.12-2018
        Функция преобразования для генерации ключей
        """
        res = Kuznechik.lsx(k, a1)
        res = Kuznechik.x([res[i] for i in range(16)], a0)
        return (res, a1.copy())
    
    @staticmethod
    def iterational_constants() -> List[List[int]]:
        """
        Формула (10) страница 4 ГОСТ Р 34.12-2018
        Генерация итерационных констант C_i
        """
        c_vec = []
        
        for i in range(1, 33):
            value = [0] * 16
            value[0] = i
            c_vec.append(Kuznechik.l(value))
        
        return c_vec
    
    @staticmethod
    def key_generate() -> Tuple[bytes, List[List[int]]]:
        """
        Генерация ключа длиной 256 бит и 10 итерационных ключей
        Возвращает: (основной_ключ_K, вектор_итерационных_ключей)
        """
        c_vec = Kuznechik.iterational_constants()
        
        # Генерация криптографически стойкого случайного ключа 256 бит (32 байта)
        k = os.urandom(32)
        k_list = list(k)
        
        k_vec = []  # Все итерационные ключи
        
        k1 = k_list[16:]
        k_vec.append(k1)
        
        k2 = k_list[:16]
        k_vec.append(k2)
        
        for i in range(1, 5):
            # F [С_8(i-1)+8]...F[С_8(i-1)+1](K_2i-1, K_2i)
            for iter_idx in range(8):
                k1, k2 = Kuznechik.fk(c_vec[8 * (i - 1) + iter_idx], k1, k2)
            
            k_vec.append(k1)
            k_vec.append(k2)
        
        return (k, k_vec)
    
    @staticmethod
    def key_generate_with_precomputed_key(key: bytes) -> Tuple[bytes, List[List[int]]]:
        """
        Генерация итерационных ключей на основе заданного основного ключа
        """
        if len(key) != 32:
            raise ValueError(f"Key length must be 32 bytes, got {len(key)}")
        
        c_vec = Kuznechik.iterational_constants()
        k_list = list(key)
        
        k_vec = []
        
        k1 = k_list[16:]
        k_vec.append(k1)
        
        k2 = k_list[:16]
        k_vec.append(k2)
        
        for i in range(1, 5):
            for iter_idx in range(8):
                k1, k2 = Kuznechik.fk(c_vec[8 * (i - 1) + iter_idx], k1, k2)
            
            k_vec.append(k1)
            k_vec.append(k2)
        
        return (key, k_vec)
    
    def encrypt(self, message: bytes) -> bytes:
        """
        Шифрование сообщения блоками длины 128 бит
        """
        if len(message) != 16:
            raise ValueError(f"Message must be 128 bits (16 bytes), got {len(message)} bytes")
        
        # Шифрование блока 128 бит (16 байт)
        a = list(message)
        
        for iter_idx in range(9):
            a = Kuznechik.lsx(self.keys[1][iter_idx], a)
        
        a = Kuznechik.x(self.keys[1][9], a)
        
        return bytes(a)
    
    def decrypt(self, message: bytes) -> bytes:
        """
        Расшифрование сообщения блоками длины 128 бит
        """
        if len(message) != 16:
            raise ValueError(f"Message must be 128 bits (16 bytes), got {len(message)} bytes")
        
        # Расшифрование блока 128 бит (16 байт)
        a = list(message)
        
        for iter_idx in range(9):
            a = Kuznechik.s_inv_l_inv_x(self.keys[1][9 - iter_idx], a)
        
        a = Kuznechik.x(self.keys[1][0], a)
        
        return bytes(a)

