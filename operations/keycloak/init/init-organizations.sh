#!/bin/sh
# Create Keycloak organizations after realm import (orgs cannot live in realm.json).
set -eu

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

create_org() {
  name="$1"
  alias="$2"
  existing="$(curl -sf "${API}/organizations?search=${alias}&exact=true" \
    -H "Authorization: Bearer ${TOKEN}" | jq -r '.[0].id // empty')"
  if [ -n "${existing}" ]; then
    echo "Organization ${alias} already exists (${existing})"
    echo "${existing}"
    return
  fi
  org_id="$(curl -sf -X POST "${API}/organizations" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d "{\"name\":\"${name}\",\"alias\":\"${alias}\",\"enabled\":true,\"domains\":[{\"name\":\"${alias}.local\"}]}" \
    -D - -o /dev/null | tr -d '\r' | awk '/^[Ll]ocation:/ {print $2}' | awk -F/ '{print $NF}')"
  if [ -z "${org_id}" ]; then
    org_id="$(curl -sf "${API}/organizations?search=${alias}&exact=true" \
      -H "Authorization: Bearer ${TOKEN}" | jq -r '.[0].id // empty')"
  fi
  echo "${org_id}"
}

add_member() {
  org_id="$1"
  username="$2"
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

ORG_A="$(create_org "Tenant A" "tenant-a")"
ORG_B="$(create_org "Tenant B" "tenant-b")"
add_member "${ORG_A}" "admin"
add_member "${ORG_A}" "alice@tenant-a.local"
add_member "${ORG_B}" "bob@tenant-b.local"

echo "Multitenancy bootstrap complete."
