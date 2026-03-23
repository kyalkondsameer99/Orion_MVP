"""Redis connection for RQ (queue) clients."""

from __future__ import annotations

from redis import Redis

from app.core.config import get_settings


def get_redis_connection() -> Redis:
    return Redis.from_url(get_settings().REDIS_URL, decode_responses=False)
