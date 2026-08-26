FROM node:latest AS build
WORKDIR /app

COPY package.json package-lock.json ./
COPY packages/ui-core/package.json packages/ui-core/
COPY frontend/app-ui/package.json frontend/app-ui/

RUN npm install --ignore-scripts --workspace=@are/ui-core --workspace=@are/app-ui

COPY packages/ui-core packages/ui-core
COPY packages/shared/src/agentic_shared/locales packages/shared/src/agentic_shared/locales
COPY frontend/app-ui frontend/app-ui
COPY openapi/ /openapi/

ARG VITE_AUTH_ENABLED=false
ARG VITE_KEYCLOAK_URL=
ARG VITE_KEYCLOAK_REALM=agentic-rag-eval
ARG VITE_KEYCLOAK_CLIENT_ID=agentic-rag-eval-ui
ENV VITE_AUTH_ENABLED=$VITE_AUTH_ENABLED
ENV VITE_KEYCLOAK_URL=$VITE_KEYCLOAK_URL
ENV VITE_KEYCLOAK_REALM=$VITE_KEYCLOAK_REALM
ENV VITE_KEYCLOAK_CLIENT_ID=$VITE_KEYCLOAK_CLIENT_ID

RUN npm run build -w @are/app-ui

FROM nginx:latest
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/frontend/app-ui/dist /usr/share/nginx/html
EXPOSE 5173
CMD ["nginx", "-g", "daemon off;"]
