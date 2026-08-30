# syntax=docker/dockerfile:1

FROM node:22-bookworm-slim AS build
WORKDIR /app

COPY package.json package-lock.json ./
COPY packages/ui-core/package.json packages/ui-core/
COPY frontend/app-ui/package.json frontend/app-ui/
COPY frontend/admin-app-ui/package.json frontend/admin-app-ui/
COPY tests/e2e/package.json tests/e2e/
COPY tests/api/package.json tests/api/
RUN npm ci --ignore-scripts --workspace=@are/admin-app-ui

COPY packages packages
COPY frontend frontend
COPY openapi openapi
COPY locales locales

ARG VITE_AUTH_ENABLED=false
ARG VITE_KEYCLOAK_URL=
ARG VITE_KEYCLOAK_REALM=agentic-rag-eval
ARG VITE_KEYCLOAK_CLIENT_ID=agentic-rag-eval-ui
ARG VITE_API_KEY=dev-admin-key-change-me
ENV VITE_AUTH_ENABLED=$VITE_AUTH_ENABLED
ENV VITE_KEYCLOAK_URL=$VITE_KEYCLOAK_URL
ENV VITE_KEYCLOAK_REALM=$VITE_KEYCLOAK_REALM
ENV VITE_KEYCLOAK_CLIENT_ID=$VITE_KEYCLOAK_CLIENT_ID
ENV VITE_API_KEY=$VITE_API_KEY

RUN npm run build -w @are/admin-app-ui

FROM nginx:1.27-alpine AS runtime
COPY frontend/admin-app-ui/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/frontend/admin-app-ui/dist /usr/share/nginx/html
EXPOSE 5173
CMD ["nginx", "-g", "daemon off;"]
