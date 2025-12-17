# InfBez - Криптографическое веб-приложение

Веб-приложение для криптографических операций с ГОСТ алгоритмами и многофакторной аутентификацией.

## Возможности

- **Шифрование**: RSA-32768, Кузнечик (ГОСТ Р 34.12-2018)
- **Хеширование**: Стрибог-512 (ГОСТ 34.11-2018)
- **Аутентификация**: Пароль + OAuth (Google/Yandex) + Email OTP
- **Интерфейсы**: Web UI + CLI
- **Безопасность**: Rate limiting, шифрование ключей, валидация данных
- **Роли**: Гость, Пользователь, Администратор

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

### Запуск через Docker (рекомендуется)

```bash
# Запуск всех сервисов
docker-compose up --build
```

Приложение доступно:

- Frontend: <http://localhost:80>
- Backend API: <http://localhost:8000>
- API Docs: <http://localhost:8000/docs>

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
│   ├── main.py         # Точка входа CLI
│   ├── utils.py        # Утилиты (Rich, форматирование)
│   └── commands/       # Команды (crypto, keys, test, server)
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
infbez --version
```

### Основные команды

```bash
# Помощь
infbez --help

# Шифрование Кузнечик
infbez crypto encrypt "Секретное сообщение" -a kuznechik

# Хеширование файла
infbez crypto hash document.pdf -f

# Комплексное тестирование всех алгоритмов
infbez test all --progress

# Запуск сервера
infbez server start --reload
```

### Команды CLI

#### crypto - Криптографические операции

- `encrypt` - Шифрование (Кузнечик, RSA)
- `decrypt` - Расшифрование
- `hash` - Хеширование (Стрибог-512)

#### keys - Управление RSA ключами

- `generate` - Генерация RSA-32768 ключей
- `list` - Список ключей
- `export` - Экспорт публичного ключа
- `import` - Импорт ключа

#### test - Тестирование и бенчмарки

- `all` - Комплексное тестирование всех алгоритмов

#### server - Управление backend

- `start` - Запуск сервера
- `init` - Инициализация БД
- `config` - Показать конфигурацию

### Примеры использования

#### Быстрое шифрование

```bash
# Шифрование
infbez crypto encrypt "Секретное сообщение" -a kuznechik -o msg.json

# Расшифрование
infbez crypto decrypt msg.json -a kuznechik -k msg.json -f
```

#### Проверка целостности файла

```bash
# Создание хеша
infbez crypto hash important.pdf -f > hash.txt

# Проверка
infbez crypto hash important.pdf -f --verify "$(cat hash.txt)"
```

#### Тестирование алгоритмов

```bash
# Все алгоритмы без RSA (RSA требует ключи)
infbez test all --skip-rsa -i 100

# Все алгоритмы включая RSA
infbez test all --rsa-keys keys.json -i 100 -o results.json

# С детализацией и прогрессом
infbez test all --progress -s 1024 -s 4096
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

## Тестирование алгоритмов

Все тесты выполняются через CLI команду `infbez test all`.

### Комплексное тестирование

```bash
# Все алгоритмы (без RSA)
infbez test all --skip-rsa

# Все алгоритмы включая RSA (требуются ключи)
infbez test all --rsa-keys keys.json

# С прогресс-баром
infbez test all --progress

# Кастомные параметры
infbez test all --rsa-keys keys.json -i 100 -s 1024 -s 4096 -o results.json
```

### Генерация RSA-32768 ключей

**ВАЖНО**: Генерация ключей RSA-32768 занимает 9-28 дней на современном CPU.

```bash
# Генерация ключей (9-28 дней)
infbez keys generate --output keys.json

# После генерации можно использовать для тестирования
infbez test all --rsa-keys keys.json
```

## Архитектура

Проект следует принципам **Clean Architecture**:

- **Routers** - HTTP эндпоинты (тонкий слой)
- **Services** - бизнес-логика (Auth, Crypto, Document)
- **Models** - ORM модели данных
- **Schemas** - валидация входных данных

Преимущества:

- Легкое тестирование (сервисы независимы от HTTP)
- Модульность (каждый сервис отвечает за одну задачу)
- Расширяемость (добавление новых алгоритмов без изменения существующих)

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
