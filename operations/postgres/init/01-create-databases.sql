-- Runs once on first Postgres container start (docker-entrypoint-initdb.d).
-- POSTGRES_DB (agentic_rag_eval) is created automatically via env.

-- Keycloak identity provider (default demo)
CREATE DATABASE keycloak;

GRANT ALL PRIVILEGES ON DATABASE keycloak TO agentic;
