# Инструкция по установке и запуску

## Требования

- Python 3.10+
- Node.js 18+
- Docker и Docker Compose
- GMP библиотека (для gmpy2)

### Установка GMP

**macOS:**
```bash
brew install gmp
```

**Ubuntu/Debian:**
```bash
sudo apt-get install libgmp-dev
```

**Windows:**
Скачайте с https://gmplib.org/

## Установка

### 1. Запуск PostgreSQL

```bash
docker-compose up -d
```

### 2. Настройка бэкенда

```bash
cd backend
pip install -r requirements.txt
```

Создайте файл `.env` на основе `.env.example`:
```bash
cp .env.example .env
# Отредактируйте .env и укажите свои настройки
```

### 3. Создание таблиц в базе данных

Таблицы создаются автоматически при первом запуске бэкенда через `Base.metadata.create_all()`.

Если нужно создать таблицы вручную через Alembic:
```bash
cd backend
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

**Примечание:** По умолчанию таблицы создаются автоматически при запуске приложения.

### 4. Установка фронтенда

```bash
cd frontend
npm install
```

Создайте файл `.env` (опционально, для кастомизации):
```
VITE_API_URL=http://localhost:8000
```

**Примечание:** По умолчанию API URL настроен в `vite.config.js` через proxy.

## Запуск

### Бэкенд

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Фронтенд

```bash
cd frontend
npm run dev
```

Фронтенд будет доступен на http://localhost:3000

Приложение будет доступно:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Первый запуск

1. Зарегистрируйте пользователя через API или создайте вручную в БД
2. Для админа установите роль в БД:
```sql
UPDATE users SET role = 'admin' WHERE username = 'your_username';
```

## Тестирование алгоритмов

Для тестирования криптографических алгоритмов с замером времени используйте CLI утилиту:

```bash
# Из корня проекта
python test_algorithms.py --all

# Тестировать конкретный алгоритм
python test_algorithms.py --streebog
python test_algorithms.py --kuznechik
python test_algorithms.py --rsa

# Настроить параметры тестирования
python test_algorithms.py --streebog --iterations 20 --data-size 16 64 256 1024

# Подробное логирование этапов работы алгоритмов
python test_algorithms.py --all --verbose
```

Утилита показывает время выполнения операций, скорость обработки данных и проверяет корректность работы алгоритмов.

**Флаги для детализации:**

- `--verbose` (`-v`) - подробное логирование всех этапов работы алгоритмов
- `--progress` (`-p`) - прогресс-бары с процентами выполнения и ETA

**Примечание:** Для более красивых прогресс-баров можно установить `tqdm`:
```bash
pip install tqdm
```

Но это необязательно - утилита работает и без него, используя простой текстовый прогресс-бар.

## Примечания

- Алгоритмы реализованы в соответствии с ГОСТ
- RSA-32768 использует GMP для длинной арифметики
- Тройная аутентификация: Пароль (Стрибог) + OAuth + Email/OTP
- Экспорт в PDF с ЭЦП реализован через reportlab

