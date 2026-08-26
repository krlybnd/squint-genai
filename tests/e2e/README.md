# UI E2E (Playwright + Gherkin)

Browser tests for the React app using **[Playwright](https://playwright.dev/)** and **[playwright-bdd](https://github.com/vitalets/playwright-bdd)**. Default execution is **headless** and **fast**; set `E2E_HEADED=1` for a visible browser.

Phase 2: does not run in default CI (`make test-unit`). Run locally or in a dedicated pipeline when the stack is up.

## Prerequisites

1. Stack reachable at `E2E_BASE_URL` (e.g. `make up-auth` → Traefik `http://localhost`).
2. Frontend built/served with the same origin (compose `frontend` or proxy).
3. For auth scenarios: Keycloak realm user (`E2E_USER` / `E2E_PASSWORD`, default `admin` / `admin`).
4. Optional: `VITE_AUTH_ENABLED=false` dev mode — set `E2E_AUTH=0` (no login; mock roles in app).

## Quick start

```bash
cd tests/e2e
cp .env.example .env
npm install
npx playwright install chromium
npm test                # fast (default)
npm run test:smoke      # @smoke scenarios only
npm run test:demo       # slow human-like cursor + video (for recordings)
npm run test:headed     # headed browser
npm run test:ui         # Playwright UI mode
```

## Feature map (6 files)

| File | Focus |
|------|--------|
| `01_auth_preferences.feature` | Login session, language + theme, logout |
| `02_documents_upload_delete.feature` | PDF upload, delete, RBAC upload button |
| `03_documents_indexing.feature` | Pending → indexed, chunk viewer (`@slow`) |
| `04_chat_sessions.feature` | New chat, send message, session drawer delete |
| `05_admin_panel.feature` | `/admin` for admin vs redirect for non-admin |
| `06_app_shell.feature` | Layout: sidebar + chat + drawer toggle |

Tags: `@e2e`, `@ui`, `@smoke` (subset), `@slow` (indexing timeouts).

## Selectors strategy

Steps use **roles and visible copy** from `frontend/src/locales/*.json` (no `data-testid` yet). For stability under i18n, scenarios either fix the locale in steps or assert translated strings from the Examples table.

Recommended follow-up (implementation): add `data-testid` on profile menu, document cards, and chat input for less brittle selectors.

## Auth personas

Steps log in via Keycloak per scenario. Default admin user: `admin` / `admin`.

| Persona | Default user | Realm roles | Used by |
|---------|--------------|-------------|---------|
| Write / admin | `E2E_USER` (`admin`) | admin, read, write | Most scenarios |
| Read-only | `bob@tenant-b.local` / `bob` | read (tenant-b) | Documents upload RBAC |
| Non-admin write | `writer@tenant-a.local` / `writer` | write | Admin panel access denied |

Override with `E2E_READONLY_*` or `E2E_NON_ADMIN_*` in `.env` when needed.

## Fixtures

- `fixtures/sample.pdf` — minimal PDF for upload scenarios.

## Reports (repo root)

After `npm run test` from `tests/e2e`:

- **HTML:** `.reports/e2e/html/index.html` — `npm run report`
- **Videos / screenshots:** `.reports/e2e/artifacts/` (one folder per test; video on every run)

## Headless vs headed

| Env | Effect |
|-----|--------|
| default | `headless: true`, fast clicks |
| `E2E_HEADED=1` | headed Chromium |
| `E2E_BASE_URL` | app origin (required) |

### Fast vs demo mode

| Command | Behavior |
|---------|----------|
| `npm test` | Fast — no artificial delays, video only on failure |
| `npm run test:demo` | Slow human-like mouse + min 20s/scenario + video on every run |

Demo env vars (set automatically by `test:demo`):

| Variable | Demo value | Fast default |
|----------|------------|--------------|
| `E2E_HUMAN` | `1` | off |
| `E2E_MIN_SCENARIO_MS` | `20000` | `0` |
| `E2E_SLOW_MO` | `500` | `0` |
| `E2E_MOUSE_STEPS` | `40` | `1` |
| `E2E_PAUSE_MS` | `450` | `0` |
| `E2E_TYPING_DELAY_MS` | `55` | `0` |

## Related

- API Gherkin: `tests/api/` (Playwright-BDD, generated OpenAPI clients, live services; `make test-api`).
- Dagger test profiles: `tools/ops` (`test-unit`, …) — e2e not included until explicitly added.
