# Redis

Celery broker + result backend.

| DB index | Use |
|----------|-----|
| `0` | Celery broker |
| `1` | Celery result backend |

Config: `redis.conf` (persisted AOF, 256mb maxmemory).
