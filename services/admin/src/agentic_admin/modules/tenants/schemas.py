from pydantic import BaseModel, Field


class CreateTenantRequest(BaseModel):
    alias: str = Field(min_length=1, max_length=255, pattern=r"^[a-zA-Z0-9_-]+$")
    name: str = Field(min_length=1, max_length=255)


class UpdateTenantRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    enabled: bool = True


class TenantOut(BaseModel):
    id: str
    alias: str
    name: str
    enabled: bool


class TenantMemberOut(BaseModel):
    id: str
    username: str
    email: str | None
    roles: list[str] = Field(default_factory=list)


class TenantMemberListResponse(BaseModel):
    items: list[TenantMemberOut]
    first: int = 0
    max: int = 50
    has_more: bool = False


class AddTenantMemberRequest(BaseModel):
    username: str = Field(min_length=1, max_length=255)
    roles: list[str] = Field(default_factory=list)


class UpdateTenantMemberRequest(BaseModel):
    roles: list[str] = Field(default_factory=list)


class TenantListResponse(BaseModel):
    items: list[TenantOut]
