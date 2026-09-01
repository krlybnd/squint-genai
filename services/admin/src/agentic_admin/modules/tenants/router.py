from agentic_shared.core.compliance.enums import AuditEventCategory
from agentic_shared.core.compliance.models import AuditEvent
from agentic_shared.core.compliance.protocols import AuditLogger
from agentic_shared.crosscut.auth.context import AuthContext
from agentic_shared.crosscut.auth.roles import AppRole
from agentic_shared.crosscut.auth.settings import AuthSettings
from agentic_shared.domains.persistence.audit_logger import emit_audit
from agentic_shared.frameworks.fastapi.dependencies.auth.dependency import require_roles
from agentic_shared.integrations.idp.core.errors import (
    IdpConflictError,
    IdpError,
    IdpForbiddenError,
    IdpNotFoundError,
)
from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, HTTPException, Query, status

from agentic_admin.modules.tenants.schemas import (
    AddTenantMemberRequest,
    CreateTenantRequest,
    TenantListResponse,
    TenantMemberListResponse,
    TenantMemberOut,
    TenantOut,
    UpdateTenantMemberRequest,
    UpdateTenantRequest,
)
from agentic_admin.modules.tenants.service import TenantAdminService

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.get("", response_model=TenantListResponse)
@inject
async def list_tenants(
    auth: FromDishka[AuthContext],
    auth_settings: FromDishka[AuthSettings],
    service: FromDishka[TenantAdminService],
) -> TenantListResponse:
    require_roles(auth, auth_settings, AppRole.ADMIN)
    try:
        items = await service.list_tenants()
        return TenantListResponse(items=items)
    except IdpForbiddenError as exc:
        raise HTTPException(
            status_code=502,
            detail=(
                "Keycloak denied Admin API access (403). Re-import the realm so the "
                "agentic-rag-eval-admin service account has realm-management roles — see "
                "operations/keycloak/README.md."
            ),
        ) from exc
    except IdpError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("", response_model=TenantOut, status_code=status.HTTP_201_CREATED)
@inject
async def create_tenant(
    body: CreateTenantRequest,
    auth: FromDishka[AuthContext],
    auth_settings: FromDishka[AuthSettings],
    service: FromDishka[TenantAdminService],
    audit: FromDishka[AuditLogger],
) -> TenantOut:
    require_roles(auth, auth_settings, AppRole.ADMIN)
    try:
        out = await service.create_tenant(alias=body.alias, name=body.name)
    except IdpConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except IdpError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    await emit_audit(
        audit,
        AuditEvent(
            category=AuditEventCategory.CONFIG_CHANGE,
            action="tenant.create",
            actor_id=auth.user_id,
            tenant_id=out.alias,
            resource_type="tenant",
            resource_id=out.alias,
        ),
    )
    return out


@router.patch("/{alias}", response_model=TenantOut)
@inject
async def update_tenant(
    alias: str,
    body: UpdateTenantRequest,
    auth: FromDishka[AuthContext],
    auth_settings: FromDishka[AuthSettings],
    service: FromDishka[TenantAdminService],
) -> TenantOut:
    require_roles(auth, auth_settings, AppRole.ADMIN)
    try:
        return await service.update_tenant(alias, name=body.name, enabled=body.enabled)
    except IdpNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except IdpError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/{alias}/members", response_model=TenantMemberListResponse)
@inject
async def list_tenant_members(
    alias: str,
    auth: FromDishka[AuthContext],
    auth_settings: FromDishka[AuthSettings],
    service: FromDishka[TenantAdminService],
    first: int = Query(0, ge=0),
    max_results: int = Query(50, ge=1, le=200, alias="max"),
) -> TenantMemberListResponse:
    require_roles(auth, auth_settings, AppRole.ADMIN)
    try:
        items, has_more = await service.list_members(alias, first=first, max_results=max_results)
        return TenantMemberListResponse(
            items=items, first=first, max=max_results, has_more=has_more
        )
    except IdpNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except IdpError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post(
    "/{alias}/members", response_model=TenantMemberOut, status_code=status.HTTP_201_CREATED
)
@inject
async def add_tenant_member(
    alias: str,
    body: AddTenantMemberRequest,
    auth: FromDishka[AuthContext],
    auth_settings: FromDishka[AuthSettings],
    service: FromDishka[TenantAdminService],
) -> TenantMemberOut:
    require_roles(auth, auth_settings, AppRole.ADMIN)
    try:
        return await service.add_member(alias, body.username, roles=body.roles)
    except IdpNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except IdpError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.patch("/{alias}/members/{username}", response_model=TenantMemberOut)
@inject
async def update_tenant_member(
    alias: str,
    username: str,
    body: UpdateTenantMemberRequest,
    auth: FromDishka[AuthContext],
    auth_settings: FromDishka[AuthSettings],
    service: FromDishka[TenantAdminService],
) -> TenantMemberOut:
    require_roles(auth, auth_settings, AppRole.ADMIN)
    try:
        return await service.update_member_roles(alias, username, body.roles)
    except IdpNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except IdpError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.delete("/{alias}/members/{username}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def remove_tenant_member(
    alias: str,
    username: str,
    auth: FromDishka[AuthContext],
    auth_settings: FromDishka[AuthSettings],
    service: FromDishka[TenantAdminService],
) -> None:
    require_roles(auth, auth_settings, AppRole.ADMIN)
    try:
        await service.remove_member(alias, username)
    except IdpNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except IdpError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.delete("/{alias}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def delete_tenant(
    alias: str,
    auth: FromDishka[AuthContext],
    auth_settings: FromDishka[AuthSettings],
    service: FromDishka[TenantAdminService],
) -> None:
    require_roles(auth, auth_settings, AppRole.ADMIN)
    try:
        await service.delete_tenant(alias)
    except IdpNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except IdpError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
