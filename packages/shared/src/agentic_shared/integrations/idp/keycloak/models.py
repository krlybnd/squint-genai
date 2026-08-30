from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ClientCredentialsTokenRequest(BaseModel):
    """OIDC client-credentials token form body (not in Admin REST OpenAPI)."""

    model_config = ConfigDict(extra="forbid")

    grant_type: Literal["client_credentials"] = "client_credentials"
    client_id: str
    client_secret: str

    def as_form(self) -> dict[str, str]:
        return self.model_dump()


class AccessTokenResponse(BaseModel):
    """OIDC token endpoint response subset (not Admin REST ``AccessToken`` claims)."""

    model_config = ConfigDict(extra="ignore")

    access_token: str = Field(min_length=1)
