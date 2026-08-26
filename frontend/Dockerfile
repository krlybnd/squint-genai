FROM node:latest AS build

COPY packages/ui-core/package.json packages/ui-core/package-lock.json /app/packages/ui-core/
RUN npm ci --ignore-scripts --prefix /app/packages/ui-core

COPY packages/ui-core /app/packages/ui-core
COPY packages/shared/src/agentic_shared/locales /app/packages/shared/src/agentic_shared/locales

WORKDIR /app/frontend/app-ui
COPY frontend/app-ui ./
RUN npm install --ignore-scripts

COPY openapi/ /openapi/

ARG VITE_AUTH_ENABLED=false
ARG VITE_KEYCLOAK_URL=
ARG VITE_KEYCLOAK_REALM=agentic-rag-eval
ARG VITE_KEYCLOAK_CLIENT_ID=agentic-rag-eval-ui
ENV VITE_AUTH_ENABLED=$VITE_AUTH_ENABLED
ENV VITE_KEYCLOAK_URL=$VITE_KEYCLOAK_URL
ENV VITE_KEYCLOAK_REALM=$VITE_KEYCLOAK_REALM
ENV VITE_KEYCLOAK_CLIENT_ID=$VITE_KEYCLOAK_CLIENT_ID

RUN node -e "\
const fs=require('fs');\
const p='public/config.json';\
const c=JSON.parse(fs.readFileSync(p,'utf8'));\
c.auth.enabled=process.env.VITE_AUTH_ENABLED==='true';\
if(process.env.VITE_KEYCLOAK_URL)c.auth.keycloakUrl=process.env.VITE_KEYCLOAK_URL;\
if(process.env.VITE_KEYCLOAK_REALM)c.auth.keycloakRealm=process.env.VITE_KEYCLOAK_REALM;\
if(process.env.VITE_KEYCLOAK_CLIENT_ID)c.auth.keycloakClientId=process.env.VITE_KEYCLOAK_CLIENT_ID;\
fs.writeFileSync(p,JSON.stringify(c,null,2)+'\n');\
"

RUN npm run build

FROM nginx:latest
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/frontend/app-ui/dist /usr/share/nginx/html
EXPOSE 5173
CMD ["nginx", "-g", "daemon off;"]
