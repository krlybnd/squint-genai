from agentic_shared.core.auth.context import AuthContext
from agentic_shared.core.auth.roles import AppRole
from agentic_shared.core.auth.settings import AuthSettings
from agentic_shared.frameworks.fastapi.auth.dependencies import require_roles
from agentic_shared.integrations.keycloak_admin.errors import (
    KeycloakAdminError,
    KeycloakConflictError,
    KeycloakForbiddenError,
    KeycloakNotFoundError,
)
from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, HTTPException, Query, status

from agentic_admin.modules.users.schemas import (
    AssignTenantRequest,
    CreateUserRequest,
    SetActiveTenantRequest,
    SetTenantRolesRequest,
    UpdateUserRequest,
    UserListResponse,
    UserOut,
)
from agentic_admin.modules.users.service import UserAdminService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=UserListResponse)
@inject
async def list_users(
    auth: FromDishka[AuthContext],
    auth_settings: FromDishka[AuthSettings],
    service: FromDishka[UserAdminService],
    search: str | None = Query(default=None),
    first: int = Query(0, ge=0),
    max_results: int = Query(50, ge=1, le=200, alias="max"),
) -> UserListResponse:
    require_roles(auth, auth_settings, AppRole.ADMIN)
    try:
        items, has_more = await service.list_users(
            search=search, first=first, max_results=max_results
        )
        return UserListResponse(items=items, first=first, max=max_results, has_more=has_more)
    except KeycloakForbiddenError as exc:
        raise HTTPException(
            status_code=502,
            detail=(
                "Keycloak denied Admin API access (403). Re-import the realm so the "
                "agentic-rag-eval-api service account has realm-management roles — see "
                "operations/keycloak/README.md."
            ),
        ) from exc
    except KeycloakAdminError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
@inject
async def create_user(
    body: CreateUserRequest,
    auth: FromDishka[AuthContext],
    auth_settings: FromDishka[AuthSettings],
    service: FromDishka[UserAdminService],
) -> UserOut:
    require_roles(auth, auth_settings, AppRole.ADMIN)
    try:
        return await service.create_user(
            username=body.username,
            email=body.email,
            password=body.password,
            realm_roles=body.realm_roles,
        )
    except KeycloakConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except KeycloakAdminError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/{username}", response_model=UserOut)
@inject
async def get_user(
    username: str,
    auth: FromDishka[AuthContext],
    auth_settings: FromDishka[AuthSettings],
    service: FromDishka[UserAdminService],
) -> UserOut:
    require_roles(auth, auth_settings, AppRole.ADMIN)
    try:
        return await service.get_user(username)
    except KeycloakNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except KeycloakAdminError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.patch("/{username}", response_model=UserOut)
@inject
async def update_user(
    username: str,
    body: UpdateUserRequest,
    auth: FromDishka[AuthContext],
    auth_settings: FromDishka[AuthSettings],
    service: FromDishka[UserAdminService],
) -> UserOut:
    require_roles(auth, auth_settings, AppRole.ADMIN)
    try:
        return await service.update_user(username, body)
    except KeycloakNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except KeycloakAdminError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/{username}/tenant", response_model=UserOut)
@inject
async def assign_user_tenant(
    username: str,
    body: AssignTenantRequest,
    auth: FromDishka[AuthContext],
    auth_settings: FromDishka[AuthSettings],
    service: FromDishka[UserAdminService],
) -> UserOut:
    require_roles(auth, auth_settings, AppRole.ADMIN)
    try:
        return await service.assign_tenant(
            username, body.alias, set_active=body.set_active, roles=body.roles
        )
    except KeycloakNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except KeycloakAdminError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.put("/{username}/tenants/{alias}/roles", response_model=UserOut)
@inject
async def set_user_tenant_roles(
    username: str,
    alias: str,
    body: SetTenantRolesRequest,
    auth: FromDishka[AuthContext],
    auth_settings: FromDishka[AuthSettings],
    service: FromDishka[UserAdminService],
) -> UserOut:
    require_roles(auth, auth_settings, AppRole.ADMIN)
    try:
        return await service.set_tenant_roles(username, alias, body.roles)
    except KeycloakNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except KeycloakAdminError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.put("/{username}/active-tenant", response_model=UserOut)
@inject
async def set_active_user_tenant(
    username: str,
    body: SetActiveTenantRequest,
    auth: FromDishka[AuthContext],
    auth_settings: FromDishka[AuthSettings],
    service: FromDishka[UserAdminService],
) -> UserOut:
    require_roles(auth, auth_settings, AppRole.ADMIN)
    try:
        return await service.set_active_tenant(username, body.alias)
    except KeycloakNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except KeycloakAdminError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.delete("/{username}/tenants/{alias}", response_model=UserOut)
@inject
async def remove_user_from_tenant(
    username: str,
    alias: str,
    auth: FromDishka[AuthContext],
    auth_settings: FromDishka[AuthSettings],
    service: FromDishka[UserAdminService],
) -> UserOut:
    require_roles(auth, auth_settings, AppRole.ADMIN)
    try:
        return await service.remove_from_tenant(username, alias)
    except KeycloakNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except KeycloakAdminError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.delete("/{username}/tenant", response_model=UserOut)
@inject
async def remove_user_tenant(
    username: str,
    auth: FromDishka[AuthContext],
    auth_settings: FromDishka[AuthSettings],
    service: FromDishka[UserAdminService],
) -> UserOut:
    require_roles(auth, auth_settings, AppRole.ADMIN)
    try:
        return await service.remove_tenant(username)
    except KeycloakNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except KeycloakAdminError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
