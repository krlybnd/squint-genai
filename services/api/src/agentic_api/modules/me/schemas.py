from pydantic import BaseModel, Field


class MembershipTenantOut(BaseModel):
    alias: str
    name: str


class MeOut(BaseModel):
    username: str
    tenant_id: str | None
    tenants: list[MembershipTenantOut] = Field(default_factory=list)


class SetMyActiveTenantRequest(BaseModel):
    alias: str = Field(min_length=1, max_length=255)
