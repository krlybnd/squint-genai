#!/bin/sh
# Drop app schema in PostgreSQL (not the keycloak database).
set -eu

: "${DATABASE_URL:=postgresql+asyncpg://agentic:agentic@postgres:5432/agentic_rag_eval}"

url="$(printf '%s' "${DATABASE_URL}" | sed 's|^postgresql+asyncpg:|postgresql:|;s|^postgresql+psycopg2:|postgresql:|')"
echo "postgres: drop schema public"
psql "$url" -v ON_ERROR_STOP=1 -c 'DROP SCHEMA IF EXISTS public CASCADE; CREATE SCHEMA public;'
echo "postgres: empty"
