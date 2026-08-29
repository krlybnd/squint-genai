from pydantic import BaseModel, Field


class CreateUserRequest(BaseModel):
    username: str = Field(min_length=1, max_length=255)
    email: str | None = Field(default=None, max_length=255)
    password: str = Field(min_length=4, max_length=128)
    realm_roles: list[str] = Field(default_factory=list)


class UpdateUserRequest(BaseModel):
    email: str | None = Field(default=None, max_length=255)
    enabled: bool | None = None
    realm_roles: list[str] | None = None
    tenant_id: str | None = Field(
        default=None,
        description="Tenant alias to assign; empty string removes tenant; omit to leave unchanged",
    )
    password: str | None = Field(default=None, min_length=4, max_length=128)


class AssignTenantRequest(BaseModel):
    alias: str = Field(min_length=1, max_length=255)
    set_active: bool | None = Field(
        default=None,
        description="Set JWT active tenant_id; default true only when user has no active tenant",
    )
    roles: list[str] | None = Field(
        default=None,
        description="App roles for this tenant membership (read/write/admin)",
    )


class SetActiveTenantRequest(BaseModel):
    alias: str = Field(min_length=1, max_length=255)


class SetTenantRolesRequest(BaseModel):
    roles: list[str] = Field(default_factory=list)


class UserOut(BaseModel):
    id: str
    username: str
    email: str | None
    enabled: bool
    tenant_id: str | None
    tenant_ids: list[str]
    realm_roles: list[str]
    tenant_roles: dict[str, list[str]] = Field(default_factory=dict)


class UserListResponse(BaseModel):
    items: list[UserOut]
    first: int = 0
    max: int = 50
    has_more: bool = False
