#!/bin/sh
# Flush Redis (broker + result backend on the same instance).
set -eu

: "${REDIS_URL:=redis://redis:6379/0}"

echo "redis: FLUSHALL (${REDIS_URL})"
redis-cli -u "${REDIS_URL}" FLUSHALL
echo "redis: empty"
