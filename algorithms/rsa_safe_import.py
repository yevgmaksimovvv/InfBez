"""
Безопасный импорт RSA модуля (не падает если нет gmpy2)
"""

def get_rsa_module():
    """
    Импортирует RSA модуль безопасно.
    Если gmpy2 не установлен, возвращает None.
    """
    try:
        from algorithms import rsa_32768
        return rsa_32768
    except (ImportError, SystemExit):
        # gmpy2 не установлен или sys.exit(1) был вызван
        return None


def get_rsa_class():
    """
    Получить класс RSA32768.
    Выбрасывает ImportError если gmpy2 не установлен.
    """
    rsa_module = get_rsa_module()
    if rsa_module is None:
        raise ImportError("Невозможно импортировать RSA: gmpy2 не установлен")
    return rsa_module.RSA32768


def is_rsa_available() -> bool:
    """Проверить доступность RSA (наличие gmpy2)"""
    return get_rsa_module() is not None
