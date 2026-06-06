from __future__ import annotations

import datetime
import logging
import threading
import time
import uuid
from datetime import timezone
from typing import Any

import jwt
import redis

from config.settings import settings

logger = logging.getLogger(__name__)

# Fallback secret if not in settings, but settings should have one.
# We'll use admin_api_key as the secret if nothing else exists,
# but it's best to have a dedicated JWT_SECRET.
JWT_SECRET = getattr(
    settings, "jwt_secret", settings.admin_api_key or "super-secret-default"
)
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24


class AuthService:
    """Service to handle JWT generation, validation, and revocation."""

    _redis_client: redis.Redis | None = None
    _in_memory_denylist: dict[str, float] = {}
    _lock = threading.Lock()

    @classmethod
    def get_redis_client(cls) -> redis.Redis | None:
        if cls._redis_client is None:
            try:
                cls._redis_client = redis.from_url(
                    settings.redis_url, decode_responses=True
                )
            except Exception as e:
                logger.error("Failed to connect to sync Redis for denylist: %s", e)
        return cls._redis_client

    @classmethod
    def is_token_revoked(cls, jti: str) -> bool:
        if settings.use_redis_sessions:
            client = cls.get_redis_client()
            if client:
                try:
                    return bool(client.exists(f"jwt:revoked:{jti}"))
                except Exception as e:
                    logger.error("Sync Redis check failed for JWT revocation: %s", e)

        # In-memory fallback
        now = time.time()
        with cls._lock:
            # Prune expired tokens
            cls._in_memory_denylist = {
                k: v for k, v in cls._in_memory_denylist.items() if v > now
            }
            return jti in cls._in_memory_denylist

    @classmethod
    def revoke_token(cls, payload: dict[str, Any]) -> None:
        jti = payload.get("jti")
        exp = payload.get("exp")
        if not jti:
            return

        now = time.time()
        ttl = int(exp - now) if exp else JWT_EXPIRATION_HOURS * 3600
        if ttl <= 0:
            return

        if settings.use_redis_sessions:
            client = cls.get_redis_client()
            if client:
                try:
                    client.setex(f"jwt:revoked:{jti}", ttl, "1")
                    return
                except Exception as e:
                    logger.error("Sync Redis token revocation failed: %s", e)

        # In-memory fallback
        with cls._lock:
            cls._in_memory_denylist[jti] = now + ttl

    @staticmethod
    def create_access_token(
        data: dict[str, Any], expires_delta: datetime.timedelta | None = None
    ) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.datetime.now(timezone.utc) + datetime.timedelta(
                hours=JWT_EXPIRATION_HOURS
            )

        expire_timestamp = int(expire.timestamp())
        to_encode.update({"exp": expire_timestamp, "jti": str(uuid.uuid4())})

        encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
        return encoded_jwt

    @staticmethod
    def decode_access_token(token: str) -> dict[str, Any] | None:
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            jti = payload.get("jti")
            if jti and AuthService.is_token_revoked(jti):
                logger.warning("Attempted to decode revoked JWT token: %s", jti)
                return None
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("JWT Expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning("Invalid JWT Token: %s", e)
            return None
