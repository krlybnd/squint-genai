from agentic_shared.crosscut.auth.claims import (
    AccessTokenClaims,
    TenantRolesMap,
    parse_access_token_claims,
    serialize_tenant_roles_json,
)
from agentic_shared.crosscut.auth.roles import AppRole
from agentic_shared.crosscut.auth.types import tenant_alias


def test_tenant_roles_map_from_json_string() -> None:
    mapped = TenantRolesMap.parse_raw_value(['{"tenant-b":["read"],"e2e":["read","write"]}'])
    assert mapped.to_role_strings() == {"tenant-b": ["read"], "e2e": ["read", "write"]}
    assert mapped.for_tenant("e2e") == frozenset({AppRole.READ, AppRole.WRITE})
    assert mapped.root[tenant_alias("tenant-b")] == frozenset({AppRole.READ})


def test_tenant_roles_map_rejects_unknown_roles() -> None:
    mapped = TenantRolesMap.parse_raw_value({"tenant-b": ["read", "unknown", "write"]})
    assert mapped.to_role_strings() == {"tenant-b": ["read", "write"]}


def test_access_token_claims_prefers_active_tenant_roles() -> None:
    claims = parse_access_token_claims(
        {
            "sub": "user-1",
            "tenant_id": "tenant-b",
            "roles": ["read", "write"],
            "tenant_roles": ['{"tenant-b":["read"],"e2e-1":["read","write"]}'],
        }
    )
    assert isinstance(claims, AccessTokenClaims)
    assert claims.tenant_id == "tenant-b"
    assert claims.user_id == "user-1"
    assert claims.app_roles() == frozenset({AppRole.READ})


def test_access_token_claims_falls_back_to_flat_roles() -> None:
    claims = parse_access_token_claims({"roles": ["write"]})
    assert claims.app_roles() == frozenset({AppRole.WRITE})


def test_access_token_claims_coerces_list_tenant_id() -> None:
    claims = parse_access_token_claims({"tenant_id": ["tenant-b"], "roles": ["read"]})
    assert claims.tenant_id == "tenant-b"


def test_serialize_tenant_roles_json() -> None:
    assert serialize_tenant_roles_json({"tenant-b": ["write", "read"]}) == [
        '{"tenant-b":["read","write"]}'
    ]
