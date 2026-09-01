#!/bin/sh
# Create Keycloak organizations after realm import (orgs cannot live in realm.json).
# Also applies declarative user profile (tenant_id, tenant_roles) and repairs demo users.
set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
REALM_DIR="$(dirname "$SCRIPT_DIR")/realm"
USER_PROFILE_JSON="${REALM_DIR}/user-profile.json"

KC_URL="${KEYCLOAK_URL:-http://keycloak:8080}"
REALM="${KEYCLOAK_REALM:-agentic-rag-eval}"
ADMIN_USER="${KEYCLOAK_ADMIN:-admin}"
ADMIN_PASS="${KEYCLOAK_ADMIN_PASSWORD:-admin}"

echo "Waiting for Keycloak at ${KC_URL}..."
until curl -sf "${KC_URL}/realms/${REALM}" >/dev/null 2>&1; do
  sleep 2
done

echo "Fetching admin token..."
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

API="${KC_URL}/admin/realms/${REALM}"

apply_user_profile() {
  if [ ! -f "${USER_PROFILE_JSON}" ]; then
    echo "Missing ${USER_PROFILE_JSON}" >&2
    exit 1
  fi
  echo "Applying declarative user profile (tenant_id, tenant_roles)..."
  curl -sf -X PUT "${API}/users/profile" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    --data-binary "@${USER_PROFILE_JSON}" >/dev/null
  echo "User profile updated."
}

# Restore demo user fields wiped by partial Admin API updates before profile fix.
repair_demo_user() {
  username="$1"
  email="$2"
  first_name="$3"
  last_name="$4"
  user_id="$(
    curl -sf "${API}/users?username=${username}&exact=true" \
      -H "Authorization: Bearer ${TOKEN}" | jq -r '.[0].id // empty'
  )"
  if [ -z "${user_id}" ]; then
    echo "Skip repair: user ${username} not found"
    return
  fi
  body="$(jq -n \
    --arg email "${email}" \
    --arg firstName "${first_name}" \
    --arg lastName "${last_name}" \
    '{email: $email, firstName: $firstName, lastName: $lastName, enabled: true}')"
  curl -sf -X PUT "${API}/users/${user_id}" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d "${body}" >/dev/null
  echo "Repaired demo user ${username}"
}

repair_demo_users() {
  echo "Repairing demo users (email / name) if needed..."
  repair_demo_user "admin" "admin@local" "Admin" "User"
  repair_demo_user "alice@tenant-a.local" "alice@tenant-a.local" "Alice" "TenantA"
  repair_demo_user "bob@tenant-b.local" "bob@tenant-b.local" "Bob" "TenantB"
}

ensure_tenant_roles_mapper() {
  scope_id="$(
    curl -sf "${API}/client-scopes" \
      -H "Authorization: Bearer ${TOKEN}" | jq -r '.[] | select(.name == "tenant") | .id // empty'
  )"
  if [ -z "${scope_id}" ]; then
    echo "Tenant client scope not found; skip tenant_roles mapper"
    return
  fi
  existing="$(
    curl -sf "${API}/client-scopes/${scope_id}/protocol-mappers/models" \
      -H "Authorization: Bearer ${TOKEN}" | jq -r '.[] | select(.name == "tenant-roles-mapper") | .id // empty'
  )"
  if [ -n "${existing}" ]; then
    echo "tenant-roles-mapper already present"
    return
  fi
  echo "Adding tenant-roles-mapper to tenant client scope..."
  curl -sf -X POST "${API}/client-scopes/${scope_id}/protocol-mappers/models" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{
      "name": "tenant-roles-mapper",
      "protocol": "openid-connect",
      "protocolMapper": "oidc-usermodel-attribute-mapper",
      "config": {
        "user.attribute": "tenant_roles",
        "claim.name": "tenant_roles",
        "jsonType.label": "String",
        "id.token.claim": "true",
        "access.token.claim": "true",
        "userinfo.token.claim": "true",
        "multivalued": "true",
        "aggregate.attrs": "false"
      }
    }' >/dev/null
  echo "tenant-roles-mapper installed."
}

sync_user_realm_roles_from_active_tenant() {
  username="$1"
  user_json="$(
    curl -sf "${API}/users?username=${username}&exact=true" \
      -H "Authorization: Bearer ${TOKEN}"
  )"
  user_id="$(echo "${user_json}" | jq -r '.[0].id // empty')"
  if [ -z "${user_id}" ]; then
    return
  fi
  tenant_id="$(echo "${user_json}" | jq -r '.[0].attributes.tenant_id[0] // empty')"
  tenant_roles_raw="$(echo "${user_json}" | jq -r '.[0].attributes.tenant_roles[0] // empty')"
  if [ -z "${tenant_roles_raw}" ] || [ -z "${tenant_id}" ]; then
    return
  fi
  desired_json="$(echo "${tenant_roles_raw}" | jq -c --arg t "${tenant_id}" '(.[$t] // []) | sort')"
  current_json="$(
    curl -sf "${API}/users/${user_id}/role-mappings/realm" \
      -H "Authorization: Bearer ${TOKEN}" \
      | jq -c '[.[].name | select(. == "admin" or . == "read" or . == "write")] | sort'
  )"
  if [ "${desired_json}" = "${current_json}" ]; then
    echo "Realm roles already match active tenant for ${username}"
    return
  fi
  echo "Syncing realm roles for ${username} (active tenant ${tenant_id})..."
  to_remove="$(jq -nr --argjson current "${current_json}" --argjson desired "${desired_json}" \
    '($current - $desired)[]')"
  to_add="$(jq -nr --argjson current "${current_json}" --argjson desired "${desired_json}" \
    '($desired - $current)[]')"
  for role in ${to_remove}; do
    role_json="$(
      curl -sf "${API}/roles/${role}" -H "Authorization: Bearer ${TOKEN}"
    )"
    curl -sf -X DELETE "${API}/users/${user_id}/role-mappings/realm" \
      -H "Authorization: Bearer ${TOKEN}" \
      -H "Content-Type: application/json" \
      -d "[${role_json}]" >/dev/null
  done
  for role in ${to_add}; do
    role_json="$(
      curl -sf "${API}/roles/${role}" -H "Authorization: Bearer ${TOKEN}"
    )"
    curl -sf -X POST "${API}/users/${user_id}/role-mappings/realm" \
      -H "Authorization: Bearer ${TOKEN}" \
      -H "Content-Type: application/json" \
      -d "[${role_json}]" >/dev/null
  done
  echo "Synced realm roles for ${username}."
}

sync_active_tenant_realm_roles() {
  echo "Syncing realm roles from tenant_roles for users with multitenancy attributes..."
  usernames="$(
    curl -sf "${API}/users?max=200" \
      -H "Authorization: Bearer ${TOKEN}" \
      | jq -r '.[] | select(.attributes.tenant_roles != null) | .username'
  )"
  for username in ${usernames}; do
    sync_user_realm_roles_from_active_tenant "${username}"
  done
}

create_org() {
  name="$1"
  alias="$2"
  existing="$(
    curl -sf "${API}/organizations?max=500" \
      -H "Authorization: Bearer ${TOKEN}" \
      | jq -r --arg alias "${alias}" '.[] | select(.alias == $alias) | .id' | head -n 1
  )"
  if [ -n "${existing}" ]; then
    echo "Organization ${alias} already exists (${existing}); syncing name '${name}'" >&2
    body="$(
      curl -sf "${API}/organizations/${existing}" \
        -H "Authorization: Bearer ${TOKEN}" \
        | jq --arg name "${name}" '.name = $name'
    )"
    echo "${body}" | curl -sf -X PUT "${API}/organizations/${existing}" \
      -H "Authorization: Bearer ${TOKEN}" \
      -H "Content-Type: application/json" \
      --data-binary @- >/dev/null \
      || echo "Failed to sync organization ${alias} name" >&2
    echo "${existing}"
    return
  fi
  org_id="$(curl -sf -X POST "${API}/organizations" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d "{\"name\":\"${name}\",\"alias\":\"${alias}\",\"enabled\":true,\"domains\":[{\"name\":\"${alias}.local\"}]}" \
    -D - -o /dev/null | tr -d '\r' | awk '/^[Ll]ocation:/ {print $2}' | awk -F/ '{print $NF}')"
  if [ -z "${org_id}" ]; then
    org_id="$(
      curl -sf "${API}/organizations?max=500" \
        -H "Authorization: Bearer ${TOKEN}" \
        | jq -r --arg alias "${alias}" '.[] | select(.alias == $alias) | .id' | head -n 1
    )"
  fi
  echo "${org_id}"
}

add_member() {
  org_id="$1"
  username="$2"
  if [ -z "${org_id}" ]; then
    echo "Skip add_member ${username}: empty org id" >&2
    return
  fi
  user_id="$(
    curl -sf "${API}/users?username=${username}&exact=true" \
      -H "Authorization: Bearer ${TOKEN}" | jq -r '.[0].id // empty'
  )"
  if [ -z "${user_id}" ]; then
    echo "User ${username} not found" >&2
    return
  fi
  curl -sf -X POST "${API}/organizations/${org_id}/members" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d "\"${user_id}\"" >/dev/null \
    || echo "Member ${username} may already belong to org"
  echo "Added ${username} to organization ${org_id}"
}

apply_user_profile
repair_demo_users
ensure_tenant_roles_mapper

ORG_A="$(create_org "Tenant A" "tenant-a")"
ORG_B="$(create_org "Tenant B" "tenant-b")"
add_member "${ORG_A}" "admin"
add_member "${ORG_B}" "admin"
add_member "${ORG_A}" "alice@tenant-a.local"
add_member "${ORG_B}" "bob@tenant-b.local"

sync_active_tenant_realm_roles

repair_demo_user_realm_roles() {
  username="$1"
  desired_json="$2"
  user_json="$(
    curl -sf "${API}/users?username=${username}&exact=true" \
      -H "Authorization: Bearer ${TOKEN}"
  )"
  user_id="$(echo "${user_json}" | jq -r '.[0].id // empty')"
  if [ -z "${user_id}" ]; then
    return
  fi
  current_json="$(
    curl -sf "${API}/users/${user_id}/role-mappings/realm" \
      -H "Authorization: Bearer ${TOKEN}" \
      | jq -c '[.[].name | select(. == "admin" or . == "read" or . == "write")] | sort'
  )"
  if [ "${desired_json}" = "${current_json}" ]; then
    return
  fi
  echo "Repairing demo realm roles for ${username}..."
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

repair_demo_user_tenant_persona() {
  username="$1"
  active_tenant="$2"
  tenant_roles_json="$3"
  realm_roles_json="$4"
  user_json="$(
    curl -sf "${API}/users?username=${username}&exact=true" \
      -H "Authorization: Bearer ${TOKEN}"
  )"
  user_id="$(echo "${user_json}" | jq -r '.[0].id // empty')"
  if [ -z "${user_id}" ]; then
    return
  fi
  body="$(echo "${user_json}" | jq -c --arg tenant "${active_tenant}" --arg roles "${tenant_roles_json}" \
    '.[0] | {
      email,
      firstName,
      lastName,
      enabled,
      attributes: ((.attributes // {}) + {
        tenant_id: [$tenant],
        tenant_roles: [$roles]
      })
    }')"
  curl -sf -X PUT "${API}/users/${user_id}" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d "${body}" >/dev/null
  echo "Reset tenant persona for ${username} (active=${active_tenant})"
  repair_demo_user_realm_roles "${username}" "${realm_roles_json}"
}

echo "Ensuring demo persona realm roles..."
repair_demo_user_tenant_persona \
  "admin" \
  "tenant-a" \
  '{"tenant-a":["admin","write","read"],"tenant-b":["admin","write","read"]}' \
  '["admin","read","write"]'
repair_demo_user_tenant_persona \
  "alice@tenant-a.local" \
  "tenant-a" \
  '{"tenant-a":["read","write"]}' \
  '["read","write"]'
repair_demo_user_tenant_persona \
  "bob@tenant-b.local" \
  "tenant-b" \
  '{"tenant-b":["read"]}' \
  '["read"]'

echo "Multitenancy bootstrap complete."
