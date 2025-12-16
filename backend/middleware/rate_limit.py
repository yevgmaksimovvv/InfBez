"""
Middleware ограничения запросов с поддержкой Redis и in-memory резервного хранилища
"""
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict
from datetime import datetime, timedelta
import logging

from backend.config import settings

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware ограничения запросов с поддержкой Redis и in-memory резервного хранилища
    """

    def __init__(self, app):
        super().__init__(app)
        self.redis = None
        self.use_redis = settings.REDIS_ENABLED

        # In-memory хранилище (резервное)
        self.requests_minute = defaultdict(list)
        self.requests_hour = defaultdict(list)

        # Строгие лимиты для критических эндпоинтов
        self.strict_endpoints = {
            "/api/auth/login": (5, 20),
            "/api/auth/register": (3, 10),
            "/api/auth/send-otp": (3, 10),
        }

    async def init_redis(self):
        """Инициализация подключения к Redis"""
        if not self.redis and self.use_redis:
            try:
                import redis.asyncio as aioredis
                self.redis = await aioredis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True,
                    socket_connect_timeout=5
                )
                await self.redis.ping()
                logger.info("Redis connection established for rate limiting")
            except ImportError:
                logger.warning("redis package not installed. Using in-memory rate limiting.")
                self.use_redis = False
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}. Using in-memory fallback.")
                self.use_redis = False
                self.redis = None

    async def dispatch(self, request: Request, call_next):
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)

        # Try to use Redis if enabled
        if self.use_redis:
            if not self.redis:
                await self.init_redis()

            if self.redis:
                return await self._redis_rate_limit(request, call_next)

        # Fallback to in-memory rate limiting
        return await self._memory_rate_limit(request, call_next)

    async def _redis_rate_limit(self, request: Request, call_next):
        """Ограничение запросов с использованием Redis"""
        client_ip = request.client.host
        path = request.url.path

        # Получение лимитов
        if path in self.strict_endpoints:
            limit_min, limit_hour = self.strict_endpoints[path]
        else:
            limit_min = settings.RATE_LIMIT_PER_MINUTE
            limit_hour = settings.RATE_LIMIT_PER_HOUR

        # Ключи Redis
        key_minute = f"ratelimit:{client_ip}:{path}:minute"
        key_hour = f"ratelimit:{client_ip}:{path}:hour"

        try:
            # Проверка и инкремент счетчиков
            pipe = self.redis.pipeline()
            pipe.incr(key_minute)
            pipe.expire(key_minute, 60)
            pipe.incr(key_hour)
            pipe.expire(key_hour, 3600)
            results = await pipe.execute()

            minute_count = results[0]
            hour_count = results[2]

            if minute_count > limit_min:
                logger.warning(f"Rate limit exceeded (per minute) for IP {client_ip} on {path}")
                raise HTTPException(
                    status_code=429,
                    detail=f"Too many requests. Limit: {limit_min} requests per minute"
                )

            if hour_count > limit_hour:
                logger.warning(f"Rate limit exceeded (per hour) for IP {client_ip} on {path}")
                raise HTTPException(
                    status_code=429,
                    detail=f"Too many requests. Limit: {limit_hour} requests per hour"
                )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Redis error in rate limiting: {e}. Falling back to in-memory.")
            self.use_redis = False
            return await self._memory_rate_limit(request, call_next)

        return await call_next(request)

    async def _memory_rate_limit(self, request: Request, call_next):
        """Ограничение запросов с использованием in-memory хранилища"""
        client_ip = request.client.host
        path = request.url.path
        now = datetime.utcnow()

        # Получение лимитов
        if path in self.strict_endpoints:
            limit_min, limit_hour = self.strict_endpoints[path]
        else:
            limit_min = settings.RATE_LIMIT_PER_MINUTE
            limit_hour = settings.RATE_LIMIT_PER_HOUR

        # Очистка старых запросов
        self._cleanup_old_requests(client_ip, now)

        # Подсчет запросов в окнах времени
        minute_count = self._count_requests_in_window(
            self.requests_minute[client_ip],
            now,
            timedelta(minutes=1)
        )
        hour_count = self._count_requests_in_window(
            self.requests_hour[client_ip],
            now,
            timedelta(hours=1)
        )

        # Проверка лимитов
        if minute_count >= limit_min:
            logger.warning(f"Rate limit exceeded (per minute) for IP {client_ip} on {path}")
            raise HTTPException(
                status_code=429,
                detail=f"Too many requests. Limit: {limit_min} requests per minute"
            )

        if hour_count >= limit_hour:
            logger.warning(f"Rate limit exceeded (per hour) for IP {client_ip} on {path}")
            raise HTTPException(
                status_code=429,
                detail=f"Too many requests. Limit: {limit_hour} requests per hour"
            )

        # Добавление текущего запроса
        self.requests_minute[client_ip].append((now, path))
        self.requests_hour[client_ip].append((now, path))

        return await call_next(request)

    def _cleanup_old_requests(self, client_ip: str, now: datetime):
        """Удаляет запросы старше 1 часа"""
        one_hour_ago = now - timedelta(hours=1)
        one_minute_ago = now - timedelta(minutes=1)

        self.requests_minute[client_ip] = [
            (ts, path) for ts, path in self.requests_minute[client_ip]
            if ts > one_minute_ago
        ]

        self.requests_hour[client_ip] = [
            (ts, path) for ts, path in self.requests_hour[client_ip]
            if ts > one_hour_ago
        ]

        if not self.requests_minute[client_ip]:
            del self.requests_minute[client_ip]
        if not self.requests_hour[client_ip]:
            del self.requests_hour[client_ip]

    def _count_requests_in_window(self, requests: list, now: datetime, window: timedelta) -> int:
        """Подсчитывает запросы в заданном временном окне"""
        cutoff = now - window
        return sum(1 for ts, _ in requests if ts > cutoff)
