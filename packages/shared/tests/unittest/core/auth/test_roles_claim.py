from agentic_shared.core.auth.roles import AppRole
from agentic_shared.core.auth.roles_claim import (
    AccessTokenClaims,
    extract_flat_keycloak_roles,
    extract_keycloak_roles,
    parse_access_token_claims,
    parse_tenant_id_from_claims,
    parse_tenant_roles_claim,
)
from agentic_shared.core.auth.tenant_roles import TenantRolesMap, serialize_tenant_roles_json


def test_parse_tenant_roles_claim_from_json_string() -> None:
    parsed = parse_tenant_roles_claim(['{"tenant-b":["read"],"e2e":["read","write"]}'])
    assert parsed == {"tenant-b": ["read"], "e2e": ["read", "write"]}


def test_tenant_roles_map_rejects_unknown_roles() -> None:
    mapped = TenantRolesMap.parse_raw_value({"tenant-b": ["read", "unknown", "write"]})
    assert mapped.to_role_strings() == {"tenant-b": ["read", "write"]}


def test_access_token_claims_model() -> None:
    claims = parse_access_token_claims(
        {
            "sub": "user-1",
            "tenant_id": "tenant-b",
            "roles": ["read", "write"],
            "tenant_roles": ['{"tenant-b":["read"],"e2e-1":["read","write"]}'],
        }
    )
    assert isinstance(claims, AccessTokenClaims)
    assert claims.active_tenant_id == "tenant-b"
    assert claims.effective_app_roles() == frozenset({AppRole.READ})


def test_extract_keycloak_roles_uses_active_tenant_roles() -> None:
    claims = {
        "tenant_id": "tenant-b",
        "roles": ["read", "write"],
        "tenant_roles": ['{"tenant-b":["read"],"e2e-1":["read","write"]}'],
    }
    assert extract_keycloak_roles(claims) == {"read"}


def test_extract_keycloak_roles_falls_back_to_flat_roles() -> None:
    claims = {"roles": ["write"]}
    assert extract_keycloak_roles(claims) == {"write"}
    assert extract_flat_keycloak_roles(claims) == {"write"}


def test_parse_tenant_id_from_claims() -> None:
    assert parse_tenant_id_from_claims({"tenant_id": "tenant-a"}) == "tenant-a"
    assert parse_tenant_id_from_claims({"tenant_id": ["tenant-b"]}) == "tenant-b"


def test_serialize_tenant_roles_json() -> None:
    assert serialize_tenant_roles_json({"tenant-b": ["write", "read"]}) == [
        '{"tenant-b":["read","write"]}'
    ]
