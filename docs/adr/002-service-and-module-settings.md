# ADR 002: Service and module settings

## Context

Each service (api, chat, admin, indexing) needs infrastructure and integration config
(Postgres, Redis, LLM, Qdrant, auth, etc.). Vertical modules and graph nodes need their
own tunables (prompts, limits, task names) with scoped env prefixes.

We previously experimented with a monolithic composed `Settings` class and Dishka
`SettingsProvider` / context injection — both added indirection without benefit.

## Decision

Three settings tiers in `agentic_shared/core/settings/`:

| Tier | Base class | Location | Loading |
|------|------------|----------|---------|
| Integration/infra | `EnvSettings` | `agentic_shared/**/settings.py` | reads `.env` on instantiate |
| Service | `AppSettings` | `services/<svc>/settings.py` | `load_settings()` → `load_app_settings(XxxSettings)` |
| Module/node | `ModuleSettings` | `modules/*/settings.py`, `core/nodes/*/settings.py` | `get_module_settings = module_settings_loader(...)` |

**Service settings** compose nested layers:

```python
class ApiSettings(AppSettings):
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    ...
```

**DI wiring:** `main.py` loads settings once, passes slices to provider constructors
(`make_service_container` lives under `frameworks/fastapi` — it injects Dishka’s
`FastapiProvider`):

```python
settings = load_settings()
make_service_container(
    DatabaseProvider(settings.database),
    AuthProvider(settings.auth, settings.role),  # frameworks.fastapi.providers.auth
    ...
)
```

No Dishka context for settings. No shared monolithic `Settings` class.

**Naming:** avoid nested field names that collide with flat env vars (e.g. use
`keycloak_integration` not `keycloak_admin` when `KEYCLOAK_ADMIN` is the Keycloak
server admin username).

## Consequences

- Each service owns only the layers it needs (indexing has no auth; admin has no Qdrant)
- Module tunables are discoverable via `env_prefix` without touching service settings
- Providers are explicit about their config dependencies in `main.py`
- Tests can construct `ApiSettings(llm=LLMSettings(...), ...)` or call `load_settings()` directly
