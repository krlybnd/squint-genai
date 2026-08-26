# ADR 005: Shared UI core and AppShell

## Context

Two Vite + React apps (`frontend/app-ui`, `frontend/admin-app-ui`) share chrome:
header/sidebar layout, bootstrap, Keycloak/dev auth, i18n, theme, and form
primitives. Duplicating that in each app produces drift (layout CSS, auth
client, locale wiring). A single mega-app would mix chat product UI with
admin CRUD.

## Decision

- **`packages/ui-core` (`@are/ui-core`)** holds shared platform UI: `AppShell`,
  `bootstrapApp` / Vite helpers, auth, i18n, preferences/theme, HTTP header
  helpers, and primitives (`Modal`, `Select`, `styles/controls.css`).
- **Each app owns product features:** chat + documents in `app-ui`; tenant/user
  admin in `admin-app-ui`. OpenAPI-generated clients stay per app.
- **Apps compose `AppShell`** and pass sidebar/content; they do not fork the
  shell markup.

## Consequences

- Layout, auth, and theme change once and apply to both UIs.
- A core change can break both apps — keep the public surface small.
- Product screens must not migrate into `ui-core`. If they do, the package
  becomes a second monolith instead of a shared shell.
