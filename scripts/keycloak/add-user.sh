#!/bin/sh
# Idempotent Keycloak user upsert (demo + live tests share the same personas).
# POSIX: runs in alpine keycloak-init and in the ops container.
set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"

KC_URL="${KEYCLOAK_URL:-http://keycloak:8080}"
REALM="${KEYCLOAK_REALM:-agentic-rag-eval}"
ADMIN_USER="${KEYCLOAK_ADMIN:-admin}"
ADMIN_PASS="${KEYCLOAK_ADMIN_PASSWORD:-admin}"
WAIT_TIMEOUT="${WAIT_TIMEOUT:-180}"

SEED=0
USERS_FILE="${DEMO_USERS_FILE:-}"
USERNAME=""
PASSWORD=""
EMAIL=""
FIRST_NAME=""
LAST_NAME=""
TENANT=""
ORGS=""
ROLES=""

usage() {
  echo "Usage:" >&2
  echo "  add-user.sh --username NAME --password PASS [options]" >&2
  echo "  add-user.sh --seed   (DEMO_USERS env, --file, or stdin)" >&2
  echo "Options: --email --first-name --last-name --tenant --orgs --roles" >&2
  echo "  --orgs  comma-separated org aliases (tenant-a,tenant-b)" >&2
  echo "  --roles tenant=role+role;tenant=role" >&2
  exit 2
}

while [ $# -gt 0 ]; do
  case "$1" in
    --seed) SEED=1; shift ;;
    --file) USERS_FILE="$2"; shift 2 ;;
    --username) USERNAME="$2"; shift 2 ;;
    --password) PASSWORD="$2"; shift 2 ;;
    --email) EMAIL="$2"; shift 2 ;;
    --first-name) FIRST_NAME="$2"; shift 2 ;;
    --last-name) LAST_NAME="$2"; shift 2 ;;
    --tenant) TENANT="$2"; shift 2 ;;
    --orgs) ORGS="$2"; shift 2 ;;
    --roles) ROLES="$2"; shift 2 ;;
    -h|--help) usage ;;
    *) echo "Unknown argument: $1" >&2; usage ;;
  esac
done

wait_keycloak() {
  elapsed=0
  until curl -sf "${KC_URL}/realms/${REALM}" >/dev/null 2>&1; do
    if [ "${elapsed}" -ge "${WAIT_TIMEOUT}" ]; then
      if [ "${OPTIONAL_SEED:-0}" = "1" ]; then
        echo "Keycloak not ready at ${KC_URL}; skip user seed"
        exit 0
      fi
      echo "Keycloak not ready at ${KC_URL}" >&2
      exit 1
    fi
    sleep 2
    elapsed=$((elapsed + 2))
  done
}

admin_token() {
  TOKEN="$(
    curl -sf -X POST "${KC_URL}/realms/master/protocol/openid-connect/token" \
      -H "Content-Type: application/x-www-form-urlencoded" \
      -d "username=${ADMIN_USER}" \
      -d "password=${ADMIN_PASS}" \
      -d "grant_type=password" \
      -d "client_id=admin-cli" \
      | jq -r .access_token
  )"
  if [ -z "${TOKEN}" ] || [ "${TOKEN}" = "null" ]; then
    echo "Failed to obtain admin token" >&2
    exit 1
  fi
}

roles_to_json() {
  spec="$1"
  if [ -z "${spec}" ]; then
    echo "{}"
    return
  fi
  printf '%s\n' "${spec}" | tr ';' '\n' | jq -R -s -c '
    split("\n")
    | map(select(length > 0))
    | map(split("="))
    | map(select(length == 2))
    | map({(.[0]): (.[1] | split("+"))})
    | add // {}
  '
}

realm_roles_for_tenant() {
  spec="$1"
  tenant="$2"
  roles_to_json "${spec}" | jq -c --arg t "${tenant}" '(.[$t] // []) | sort'
}

lookup_user_id() {
  curl -sf "${API}/users?username=${1}&exact=true" \
    -H "Authorization: Bearer ${TOKEN}" | jq -r '.[0].id // empty'
}

lookup_org_id() {
  curl -sf "${API}/organizations?max=500" \
    -H "Authorization: Bearer ${TOKEN}" \
    | jq -r --arg alias "$1" '.[] | select(.alias == $alias) | .id' | head -n 1
}

sync_realm_roles() {
  user_id="$1"
  desired_json="$2"
  current_json="$(
    curl -sf "${API}/users/${user_id}/role-mappings/realm" \
      -H "Authorization: Bearer ${TOKEN}" \
      | jq -c '[.[].name | select(. == "admin" or . == "read" or . == "write")] | sort'
  )"
  if [ "${desired_json}" = "${current_json}" ]; then
    return
  fi
  to_remove="$(jq -nr --argjson current "${current_json}" --argjson desired "${desired_json}" \
    '($current - $desired)[]')"
  to_add="$(jq -nr --argjson current "${current_json}" --argjson desired "${desired_json}" \
    '($desired - $current)[]')"
  for role in ${to_remove}; do
    role_json="$(curl -sf "${API}/roles/${role}" -H "Authorization: Bearer ${TOKEN}")"
    curl -sf -X DELETE "${API}/users/${user_id}/role-mappings/realm" \
      -H "Authorization: Bearer ${TOKEN}" \
      -H "Content-Type: application/json" \
      -d "[${role_json}]" >/dev/null
  done
  for role in ${to_add}; do
    role_json="$(curl -sf "${API}/roles/${role}" -H "Authorization: Bearer ${TOKEN}")"
    curl -sf -X POST "${API}/users/${user_id}/role-mappings/realm" \
      -H "Authorization: Bearer ${TOKEN}" \
      -H "Content-Type: application/json" \
      -d "[${role_json}]" >/dev/null
  done
}

add_org_member() {
  user_id="$1"
  org_alias="$2"
  org_id="$(lookup_org_id "${org_alias}")"
  if [ -z "${org_id}" ]; then
    echo "Skip org ${org_alias}: not found (create tenants first)" >&2
    return
  fi
  curl -sf -X POST "${API}/organizations/${org_id}/members" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d "\"${user_id}\"" >/dev/null \
    || true
}

ensure_user() {
  username="$1"
  password="$2"
  email="$3"
  first_name="$4"
  last_name="$5"
  tenant="$6"
  orgs="$7"
  roles_spec="$8"

  tenant_roles_json="$(roles_to_json "${roles_spec}")"
  body="$(jq -n \
    --arg username "${username}" \
    --arg email "${email}" \
    --arg firstName "${first_name}" \
    --arg lastName "${last_name}" \
    --arg tenant "${tenant}" \
    --arg roles "${tenant_roles_json}" \
    '{
      username: $username,
      email: $email,
      firstName: $firstName,
      lastName: $lastName,
      enabled: true,
      emailVerified: true,
      attributes: {
        tenant_id: (if $tenant == "" then [] else [$tenant] end),
        tenant_roles: (if $roles == "{}" then [] else [$roles] end)
      }
    }')"

  user_id="$(lookup_user_id "${username}")"
  if [ -z "${user_id}" ]; then
    tmp="$(mktemp)"
    code="$(curl -sS -o "${tmp}" -w '%{http_code}' -X POST "${API}/users" \
      -H "Authorization: Bearer ${TOKEN}" \
      -H "Content-Type: application/json" \
      -d "${body}")"
    rm -f "${tmp}"
    if [ "${code}" != "201" ] && [ "${code}" != "409" ]; then
      echo "Failed to create user ${username}: HTTP ${code}" >&2
      exit 1
    fi
    user_id="$(lookup_user_id "${username}")"
  else
    curl -sf -X PUT "${API}/users/${user_id}" \
      -H "Authorization: Bearer ${TOKEN}" \
      -H "Content-Type: application/json" \
      -d "${body}" >/dev/null
  fi
  if [ -z "${user_id}" ]; then
    echo "User ${username} could not be resolved after upsert" >&2
    exit 1
  fi

  pwd_json="$(jq -n --arg v "${password}" '{type:"password",value:$v,temporary:false}')"
  curl -sf -X PUT "${API}/users/${user_id}/reset-password" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d "${pwd_json}" >/dev/null

  if [ -n "${tenant}" ]; then
    desired="$(realm_roles_for_tenant "${roles_spec}" "${tenant}")"
    sync_realm_roles "${user_id}" "${desired}"
  fi

  old_ifs="${IFS}"
  IFS=','
  for org_alias in ${orgs}; do
    IFS="${old_ifs}"
    [ -n "${org_alias}" ] || continue
    add_org_member "${user_id}" "${org_alias}"
    IFS=','
  done
  IFS="${old_ifs}"

  echo "User ${username} ready"
}

seed_catalog() {
  if [ -n "${USERS_FILE}" ] && [ -f "${USERS_FILE}" ]; then
    cat "${USERS_FILE}"
  elif [ -n "${DEMO_USERS:-}" ]; then
    printf '%s\n' "${DEMO_USERS}"
  elif [ ! -t 0 ]; then
    cat
  else
    echo "Missing user catalog (DEMO_USERS, --file, or stdin)" >&2
    exit 1
  fi
}

seed_users() {
  echo "Seeding users..."
  tmp="$(mktemp)"
  seed_catalog > "${tmp}"
  while IFS= read -r line || [ -n "${line}" ]; do
    case "${line}" in
      ''|\#*) continue ;;
    esac
    username="${line%%|*}"
    rest="${line#*|}"
    password="${rest%%|*}"
    rest="${rest#*|}"
    email="${rest%%|*}"
    rest="${rest#*|}"
    first_name="${rest%%|*}"
    rest="${rest#*|}"
    last_name="${rest%%|*}"
    rest="${rest#*|}"
    tenant="${rest%%|*}"
    rest="${rest#*|}"
    orgs="${rest%%|*}"
    roles_spec="${rest#*|}"
    ensure_user "${username}" "${password}" "${email}" "${first_name}" "${last_name}" "${tenant}" "${orgs}" "${roles_spec}"
  done < "${tmp}"
  rm -f "${tmp}"
}

wait_keycloak
admin_token
API="${KC_URL}/admin/realms/${REALM}"

if [ "${SEED}" -eq 1 ]; then
  seed_users
  exit 0
fi

if [ -z "${USERNAME}" ] || [ -z "${PASSWORD}" ]; then
  usage
fi
EMAIL="${EMAIL:-${USERNAME}}"
ensure_user "${USERNAME}" "${PASSWORD}" "${EMAIL}" "${FIRST_NAME}" "${LAST_NAME}" "${TENANT}" "${ORGS}" "${ROLES}"
