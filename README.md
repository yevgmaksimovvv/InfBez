# InfBez - Криптографическое веб-приложение

Веб-приложение для криптографических операций с ГОСТ алгоритмами и тройной аутентификацией.


## Возможности

- **Шифрование**: RSA-32768, Кузнечик (ГОСТ Р 34.12-2018)
- **Хеширование**: Стрибог-512 (ГОСТ 34.11-2018)
- **Аутентификация**: Пароль + OAuth (Google/Yandex) + Email OTP
- **Безопасность**: Rate limiting, шифрование ключей, валидация данных
- **Роли**: Гость, Пользователь, Администратор

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

### Запуск

```bash
# 1. Запустить PostgreSQL
docker-compose up -d postgres

# 2. Создать таблицы БД
cd backend
python migration_helper.py

# 3. Создать .env файл
cat > .env << 'EOF'
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/cybersecurity
SECRET_KEY=your-secret-key-change-this
MASTER_KEY=your-master-key-for-encryption
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
OTP_EXPIRE_MINUTES=5
EOF

# 4. Установить зависимости и запустить backend
pip install -r requirements.txt
uvicorn main:app --reload

# 5. Установить и запустить frontend
cd ../frontend
npm install
npm run dev
```

Приложение доступно:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Запуск через Docker

```bash
docker-compose up --build
```

Приложение доступно:
- Frontend: http://localhost:80
- Backend: http://localhost:8000

## Структура проекта

```
InfBez/
├── backend/              # FastAPI backend
│   ├── core/            # Ядро приложения
│   │   ├── database.py          # База данных
│   │   ├── encryption.py        # Шифрование ключей
│   │   └── security/            # Модули безопасности
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
│   ├── kuznechik/      # Кузнечик
│   ├── streebog/       # Стрибог
│   └── rsa_32768.py    # RSA-32768
└── docker-compose.yml   # Docker конфигурация
```

Подробное описание архитектуры смотри в [ARCHITECTURE.md](ARCHITECTURE.md).

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

Ответ:
```json
{
  "encrypted": "9f8e7d6c...",
  "key_id": "550e8400-e29b-41d4-a716-446655440000",
  "algorithm": "rsa"
}
```

### Расшифрование (RSA)

```bash
curl -X POST http://localhost:8000/api/crypto/decrypt \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "encrypted_data": "9f8e7d6c...",
    "algorithm": "rsa",
    "key_id": "550e8400-e29b-41d4-a716-446655440000"
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

### Реализовано

- Приватные RSA ключи шифруются мастер-ключом и не передаются клиенту
- OTP коды хешируются перед сохранением (Стрибог-512)
- Rate limiting: 60 req/min общий, специальные лимиты для login/register
- Валидация всех входных данных
- Структурированное логирование в `logs/app.log`
- JWT токены для аутентификации

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

```bash
# Все алгоритмы
python test_algorithms.py --all

# Конкретный алгоритм
python test_algorithms.py --streebog
python test_algorithms.py --kuznechik
python test_algorithms.py --rsa

# С детализацией
python test_algorithms.py --all --verbose --progress
```

## Технологии

- **Backend**: FastAPI, Python 3.10+, PostgreSQL
- **Frontend**: React, Tailwind CSS
- **Алгоритмы**: RSA-32768 (GMP), Кузнечик, Стрибог-512
- **Инфраструктура**: Docker, Nginx

## Production рекомендации

- Настроить HTTPS/SSL (Let's Encrypt)
- Изменить `SECRET_KEY` и `MASTER_KEY` на криптостойкие
- Настроить connection pooling для БД
- Добавить мониторинг (Prometheus/Sentry)
- Завершить интеграцию OAuth
- Настроить автоматические бэкапы БД
- Добавить unit/integration тесты

## Архитектура

Проект следует принципам **Clean Architecture** с разделением на слои:
- **Routers** - HTTP эндпоинты
- **Services** - бизнес-логика
- **Models** - структура данных
- **Schemas** - валидация

Детали в [ARCHITECTURE.md](ARCHITECTURE.md).

## Лицензия

Проект создан в учебных целях.
