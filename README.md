# InfBez - Криптографическое веб-приложение

Веб-приложение для криптографических операций с ГОСТ алгоритмами и многофакторной аутентификацией.

## Содержание

- [Возможности](#возможности)
- [Технологии](#технологии)
- [Быстрый старт](#быстрый-старт)
  - [Web-приложение (Docker)](#запуск-сервера-через-docker-compose-рекомендуется)
  - [CLI интерфейс](#cli---интерфейс-командной-строки)
- [Структура проекта](#структура-проекта)
- [CLI - Интерфейс командной строки](#cli---интерфейс-командной-строки)
  - [Команды Кузнечик](#kuznechik---шифрование-кузнечик-гост-р-341122018)
  - [Команды RSA](#rsa---rsa-32768)
  - [Команды Стрибог](#streebog---хеширование-стрибог-512-гост-34112018)
- [API примеры](#api-примеры)
- [Безопасность](#безопасность)
- [Генерация RSA-32768 ключей](#генерация-rsa-32768-ключей)
- [Архитектура](#архитектура)
- [Production рекомендации](#production-рекомендации)

## Возможности

- **Шифрование**: RSA-32768, Кузнечик (ГОСТ Р 34.12-2018)
- **Хеширование**: Стрибог-512 (ГОСТ 34.11-2018)
- **Аутентификация**: Пароль + OAuth (Google/Yandex) + Email OTP
- **Интерфейсы**: Web UI + CLI
- **Безопасность**: Rate limiting, шифрование ключей, валидация данных
- **Роли**: Гость, Пользователь, Администратор

### Быстрые примеры CLI

```bash
# Установка CLI
pip install -e .

# Шифрование
kuznechik encrypt "Секретное сообщение"
encrypt document.txt -o encrypted.json

# Хеширование
streebog hash important.pdf

# RSA ключи
rsa keygen -o my_keys.json
rsa keys  # Показать все ключи
```

## Технологии

- **Backend**: FastAPI, Python 3.10+, PostgreSQL, SQLAlchemy
- **Frontend**: React 18, Vite, Tailwind CSS
- **Криптография**: RSA-32768 (GMP), Кузнечик, Стрибог-512
- **Инфраструктура**: Docker, Nginx

## Быстрый старт

### Требования

- Python 3.10+
- Node.js 18+
- Docker и Docker Compose
- GMP библиотека (для RSA)

### Установка GMP

```bash
# macOS
brew install gmp

# Ubuntu/Debian
sudo apt-get install libgmp-dev
```

### Запуск сервера через Docker Compose (рекомендуется)

Backend сервер запускается **только через Docker Compose**:

```bash
# Запуск всех сервисов (PostgreSQL, Redis, Backend, Frontend)
docker-compose up --build

# Или в фоновом режиме
docker-compose up -d --build

# Остановка
docker-compose down

# Просмотр логов
docker-compose logs -f backend
```

Приложение доступно:

- Frontend: <http://localhost:80>
- Backend API: <http://localhost:8000>
- API Docs: <http://localhost:8000/docs>
- PostgreSQL: <http://localhost:5432>
- Redis: <http://localhost:6379>

### Локальный запуск

```bash
# 1. Запустить PostgreSQL
docker-compose up -d postgres

# 2. Настроить backend
cd backend
cp ../.env.example .env
# Отредактируйте .env файл

# 3. Создать таблицы БД
python migration_helper.py

# 4. Установить зависимости и запустить backend
pip install -r ../requirements.txt  # Используем централизованный файл
uvicorn main:app --reload

# 5. Установить и запустить frontend
cd ../frontend
npm install
npm run dev
```

Приложение доступно:

- Frontend: <http://localhost:5173>
- Backend API: <http://localhost:8000>
- API Docs: <http://localhost:8000/docs>

## Структура проекта

```text
InfBez/
├── backend/              # FastAPI backend
│   ├── core/            # Ядро (database, encryption, security)
│   ├── models/          # ORM модели (User, RSAKeyPair, Document)
│   ├── schemas/         # Pydantic схемы валидации
│   ├── services/        # Бизнес-логика (Auth, Crypto, Document)
│   ├── routers/         # API endpoints
│   ├── middleware/      # Rate limiting
│   └── main.py          # Точка входа
├── frontend/            # React frontend
│   ├── src/
│   │   ├── pages/       # Страницы
│   │   ├── components/  # Компоненты
│   │   └── services/    # API клиент
│   └── nginx.conf       # Nginx конфиг
├── algorithms/          # ГОСТ алгоритмы
│   ├── kuznechik/      # Кузнечик (ГОСТ Р 34.12-2018)
│   ├── streebog/       # Стрибог-512 (ГОСТ 34.11-2018)
│   └── rsa_32768.py    # RSA-32768 (GMP)
├── cli/                 # Интерфейс командной строки
│   ├── commands/       # Команды (kuznechik, rsa, streebog, universal)
│   ├── services/       # Бизнес-логика криптографии
│   ├── utils.py        # Утилиты (Rich, форматирование)
│   └── exit_codes.py   # Коды возврата для CLI
├── results/             # Выходные файлы (ключи, зашифрованные данные)
├── requirements.txt     # Централизованные зависимости
├── requirements-dev.txt # Зависимости для разработки
├── setup.py            # Установка CLI пакета
└── docker-compose.yml   # Docker конфигурация
```

Подробное описание архитектуры: [ARCHITECTURE.md](ARCHITECTURE.md)

## Управление зависимостями

Все зависимости централизованы в корне проекта:

- **requirements.txt** - основные зависимости (backend, алгоритмы, CLI)
- **requirements-dev.txt** - дополнительные инструменты для разработки (pytest, black, flake8)
- **setup.py** - установка CLI пакета

### Установка

```bash
# Production
pip install -r requirements.txt

# Development (включает production)
pip install -r requirements-dev.txt

# CLI пакет
pip install -e .              # базовая установка
pip install -e ".[dev]"       # с dev инструментами
```

### Добавление зависимостей

1. Добавьте пакет в `requirements.txt` (или `requirements-dev.txt` для dev-инструментов)
2. Укажите версию: `==` для точной, `>=` для минимальной
3. Добавьте комментарий с назначением пакета
4. Пересоберите Docker: `docker-compose build backend`

## CLI - Интерфейс командной строки

### Установка CLI

```bash
# Dev режим (рекомендуется)
pip install -e .

# Проверка установки
kuznechik --help
rsa --help
streebog --help
encrypt --help
```

### Основные команды

CLI использует **прямые команды без префикса**, что делает их короче и удобнее:

```bash
# Шифрование Кузнечик
kuznechik encrypt "Секретное сообщение"

# Хеширование файла
streebog hash document.pdf

# Генерация RSA ключей
rsa keygen -o my_keys.json

# Универсальные команды
encrypt "text"
hash "data"
```

### Структура команд

#### kuznechik - Шифрование Кузнечик (ГОСТ Р 34.12-2018)

```bash
kuznechik encrypt <text|file> [-o output]
kuznechik decrypt <file> [-o output] [--key keyfile]
```

#### rsa - RSA-32768

```bash
rsa encrypt <text|file> --key <pubkey> [-o output]
rsa decrypt <file> --key <privkey> [-o output]
rsa keygen [-o output] [--name name]
rsa keys [--directory dir]
rsa export <keyfile> [-o output] [--public]
rsa import <keyfile> [-o output]
```

#### streebog - Хеширование Стрибог-512 (ГОСТ 34.11-2018)

```bash
streebog hash <text|file> [--hex/--base64]
streebog verify <file> <hash>
```

#### Универсальные команды (короткие алиасы)

```bash
encrypt <text|file>     # Использует Кузнечик
decrypt <file>          # Автоопределение алгоритма
```

**Примечание**: Команда `hash` зарегистрирована, но может конфликтовать с bash builtin. Используйте `streebog hash` для хеширования.

### Примеры использования

#### Быстрое шифрование Кузнечик

```bash
# Шифрование текста
kuznechik encrypt "Секретное сообщение"

# Шифрование файла
kuznechik encrypt document.txt -o encrypted.json

# Расшифрование (ключ автоматически берется из файла)
kuznechik decrypt encrypted.json

# Расшифрование с выводом в файл
kuznechik decrypt encrypted.json -o decrypted.txt
```

#### RSA-32768 шифрование

```bash
# Генерация ключей (демо режим)
rsa keygen -o my_keys.json --name "My Key"

# Список ключей
rsa keys

# Экспорт публичного ключа
rsa export my_keys.json -o public.json

# Шифрование
rsa encrypt "Secret" --key public.json -o encrypted.json

# Расшифрование
rsa decrypt encrypted.json --key my_keys.json
```

#### Проверка целостности файла

```bash
# Создание хеша
streebog hash important.pdf

# Проверка хеша
streebog verify important.pdf "9a8b7c6d..."

# Хеш в base64
streebog hash file.txt --base64
```

### Дополнительные возможности CLI

#### Общие опции

Все команды поддерживают:
- `--force` / `-f` - Перезапись существующих файлов без подтверждения
- `-o` / `--output` - Указание пути для выходного файла
- `-h` / `--help` - Справка по команде

```bash
# Перезапись файла
kuznechik encrypt "text" -o result.json --force

# Справка
rsa keygen --help
```

#### Коды возврата

CLI использует стандартизированные коды возврата ([cli/exit_codes.py](cli/exit_codes.py)):

- `0` - Успешное выполнение
- `1` - Общая ошибка
- `2` - Ошибка чтения файла
- `3` - Ошибка записи файла
- `10` - Ошибка шифрования
- `11` - Ошибка расшифрования
- `12` - Ошибка хеширования
- `20` - Невалидный ключ
- `30` - Данные слишком большие

Это позволяет использовать CLI в скриптах с надежной обработкой ошибок.

```bash
# Пример использования в скриптах
if kuznechik encrypt "data" -o output.json; then
    echo "Шифрование успешно"
else
    echo "Ошибка: код $?"
fi
```

## API примеры

### Регистрация

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "user",
    "email": "user@example.com",
    "password": "password123"
  }'
```

### Вход

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"user","password":"password123"}'
```

### Шифрование (RSA)

```bash
curl -X POST http://localhost:8000/api/crypto/encrypt \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Secret message",
    "algorithm": "rsa"
  }'
```

### Хеширование (Стрибог)

```bash
curl -X POST http://localhost:8000/api/crypto/hash \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, World!"}'
```

## Безопасность

### Реализованные меры

- Приватные RSA ключи шифруются мастер-ключом
- OTP коды хешируются перед сохранением (Стрибог-512)
- JWT токены для аутентификации
- Rate limiting на всех эндпоинтах
- Валидация всех входных данных
- Структурированное логирование

### Rate Limits

| Endpoint | Минута | Час |
|----------|--------|-----|
| Общий лимит | 60 | 1000 |
| `/api/auth/login` | 5 | 20 |
| `/api/auth/register` | 3 | 10 |
| `/api/auth/send-otp` | 3 | 10 |

### Лимиты размеров данных

- RSA: максимум 4090 байт
- Кузнечик: максимум 1MB
- Общий лимит: 100KB

## Генерация RSA-32768 ключей

**ВАЖНО**: Генерация ключей RSA-32768 занимает 5-20 дней на современном CPU.

Проект включает полную реализацию генерации ключей с параллелизацией:

```bash
# Генерация RSA-32768 ключей (займет несколько дней!)
rsa keygen -o keys.json --name "Production Key"

# Генерация с кастомными параметрами
rsa keygen -o keys.json --rounds 20 --no-parallel

# Список ключей (ищет в ./keys и текущей директории)
rsa keys

# Список ключей в конкретной директории
rsa keys -d ./my_keys

# Процесс генерации:
# - Параллельная генерация простых чисел p и q (16384 бит каждое)
# - Miller-Rabin тест простоты (15 раундов по умолчанию)
# - Логирование прогресса каждые 30 секунд
# - Полная статистика по завершении
```

### Хранение результатов

По умолчанию все результаты криптографических операций сохраняются:
- **Зашифрованные данные**: `encrypted.json` (или указанный через `-o` путь)
- **RSA ключи**: `rsa_keys.json` (можно указать кастомное имя)
- **Рекомендуемая директория**: [results/](results/) - создана для хранения всех выходных файлов

#### Формат выходных файлов

Все результаты сохраняются в JSON с метаданными:

```json
{
  "encrypted": "base64_encrypted_data",
  "key": "base64_key",
  "algorithm": "kuznechik",
  "encoding": "base64",
  "original_size": 1024,
  "encrypted_size": 1040,
  "timestamp": "2025-12-18T10:00:00Z"
}
```

Это обеспечивает:
- Самодостаточность файлов (ключ включен)
- Прозрачность (видны размеры и алгоритм)
- Отслеживаемость (timestamp для аудита)

Для тестирования и разработки используйте готовые ключи или RSA с меньшим размером.

## Архитектура

Проект следует принципам **Clean Architecture** и **Separation of Concerns**:

### Backend архитектура

- **Routers** - HTTP эндпоинты (тонкий слой)
- **Services** - бизнес-логика (Auth, Crypto, Document)
- **Models** - ORM модели данных
- **Schemas** - валидация входных данных

### CLI архитектура

CLI построен на модульной архитектуре с разделением ответственности:

```text
cli/
├── commands/              # Обработчики команд (UI слой)
│   ├── kuznechik.py      # Команды Кузнечик
│   ├── rsa.py            # Команды RSA
│   ├── streebog.py       # Команды Стрибог
│   └── universal.py      # Универсальные алиасы
├── services/             # Бизнес-логика (без зависимости от CLI)
│   └── crypto_service.py # KuznechikService, RSAService, StreebogService
├── utils.py              # Утилиты (Rich форматирование, I/O)
└── exit_codes.py         # Стандартизированные коды возврата
```

**Ключевые принципы:**
- **Commands** - только CLI интерфейс (парсинг аргументов, вывод)
- **Services** - чистая бизнес-логика (можно переиспользовать)
- **Утилиты** - общие функции (форматирование, файловый I/O)
- **Exit codes** - явные коды ошибок для скриптов

Преимущества:

- Легкое тестирование (сервисы независимы от CLI)
- Модульность (каждый сервис отвечает за одну задачу)
- Расширяемость (добавление новых алгоритмов без изменения существующих)
- Переиспользование (CLI и Backend используют одни алгоритмы)

Детали в [ARCHITECTURE.md](ARCHITECTURE.md)

## Production рекомендации

### Обязательно

1. Настроить HTTPS/SSL (Let's Encrypt)
2. Изменить `SECRET_KEY` и `MASTER_KEY` на криптостойкие
3. Настроить автоматические бэкапы БД
4. Добавить мониторинг (Prometheus/Sentry)

### Рекомендуется

- Настроить connection pooling для БД
- Завершить интеграцию OAuth
- Добавить unit/integration тесты
- Настроить CI/CD pipeline

## Лицензия

Проект создан в учебных целях.
