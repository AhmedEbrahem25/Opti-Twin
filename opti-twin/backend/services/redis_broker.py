"""
Redis Pub/Sub broker — wraps both publish (control) and async subscribe
(telemetry, recommendations) for the FastAPI gateway.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import AsyncIterator, Optional

import redis.asyncio as aioredis

log = logging.getLogger("opti-twin.redis")


REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))


class RedisBroker:
    def __init__(self) -> None:
        self.client: Optional[aioredis.Redis] = None

    async def connect(self) -> None:
        self.client = aioredis.Redis(
            host=REDIS_HOST, port=REDIS_PORT, decode_responses=True
        )
        await self.client.ping()
        log.info("Redis connected — %s:%s", REDIS_HOST, REDIS_PORT)

    async def disconnect(self) -> None:
        if self.client:
            await self.client.close()
            log.info("Redis connection closed")

    async def publish(self, channel: str, payload: dict) -> None:
        if not self.client:
            await self.connect()
        await self.client.publish(channel, json.dumps(payload))  # type: ignore[union-attr]

    async def subscribe(self, *channels: str) -> AsyncIterator[tuple[str, dict]]:
        if not self.client:
            await self.connect()
        pubsub = self.client.pubsub()  # type: ignore[union-attr]
        await pubsub.subscribe(*channels)
        try:
            async for msg in pubsub.listen():
                if msg.get("type") != "message":
                    continue
                channel = msg["channel"]
                try:
                    data = json.loads(msg["data"])
                except Exception:
                    continue
                yield channel, data
        finally:
            await pubsub.unsubscribe(*channels)
            await pubsub.close()
