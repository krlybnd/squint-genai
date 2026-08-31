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
cp tests/e2e/.env.example tests/e2e/.env
npx playwright install chromium
make -C tests/e2e run-smoke-suite        # @smoke
make -C tests/e2e run-regression-suite   # @regression
make -C tests/e2e run                    # smoke then regression
make e2e                                 # same as tests/e2e run
```

npm equivalents from the repo root: `npm run test:smoke -w agentic-rag-eval-e2e`, `test:regression`, `test` (all tags), `test:demo`, `test:headed`, `test:ui`.

## Feature map

| File | Focus |
|------|--------|
| `01_auth_preferences.feature` | Login session, language + theme, logout |
| `02_documents_upload_delete.feature` | PDF upload, delete, RBAC upload button |
| `03_documents_indexing.feature` | Pending → indexed, chunk viewer (`@slow`) |
| `04_chat_sessions.feature` | New chat, send message, session drawer delete |
| `05_admin_panel.feature` | `/admin` for admin vs redirect for non-admin |
| `06_app_shell.feature` | Layout: sidebar + chat + drawer toggle |
| `07_admin_tenant_membership.feature` | Create tenant, assign alice with read/write, verify on tenant members |

Tags: `@e2e`, `@ui`, `@smoke` / `@regression` (disjoint suites), `@slow` (indexing).

## Step vocabulary

Features name **visible copy and paths**. Replay a scenario in the English UI without opening `steps/`. Shared steps live in `steps/ui.steps.ts` and `steps/auth.steps.ts`.

| Step | Example |
|------|---------|
| Sign in | `Given I am signed in as "admin"` (also `"bob@tenant-b.local"`, `"writer@tenant-a.local"`) |
| Go / reload | `When I go to "/"`, `When I reload the page` |
| Click | `When I click the button "New chat"`, `When I click the menu item "Admin panel"` |
| Choose (radio) | `When I choose "Magyar"` |
| Fill / type | `When I fill "Alias" with "tenant-a"`, `When I type "Hello" into "Ask a question…" and press Enter` |
| See | `Then I should see "No documents yet"`, `Then I should see the heading "Documents"`, `Then I should see the button "Upload PDF"` |
| Path | `Then I should be on "/admin"`, `Then I should be on a page matching "/realms/"` |
| Theme / storage | `Then the page theme should be "neptune"`, `Then local storage "app-locale" should be "hu"` |

Domain leftovers (still parameterized) are only where the UI is not a named control: document cards and status, file upload, session delete, unique tenant alias.

Do not add a new step that exists only for one scenario — extend the table above or put the label in the feature.

## Selectors strategy

Steps resolve **roles and visible copy** from `locales/**/*.json`. Scenarios pin English unless they switch language and then use the translated string (e.g. logout `"Kijelentkezés"` after `"Magyar"`).

## Auth personas

Steps log in via Keycloak per scenario. Default admin user: `admin` / `admin`.

| Persona | Default user | Realm roles | Used by |
|---------|--------------|-------------|---------|
| Write / admin | `E2E_USER` (`admin`) | admin, read, write | Most scenarios |
| Read-only | `bob@tenant-b.local` / `bob` | read (tenant-b) | Documents upload RBAC |
| Non-admin write | `writer@tenant-a.local` / `writer` | write | Admin panel access denied |

Override with `E2E_READONLY_*` or `E2E_NON_ADMIN_*` in `.env` when needed.

## Fixtures

Fictional **Pineford Gazette** clippings (extractable text, not empty pages):

| File | Story |
|------|--------|
| `fixtures/sample_1.pdf` | 12 March 2024 — Maple Street Bakery / Marta Kovacs wins the pie contest |
| `fixtures/sample_2.pdf` | 18 March 2024 — river ferry resumes Sunday, Captain Nia Brooks |

Upload/delete and indexing use `sample_1.pdf`. The document-actions scenario uses `sample_2.pdf`. Chat asks who won the pie contest after `sample_1.pdf` is indexed.

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
