from pydantic import BaseModel, Field


class DetokenizeRequest(BaseModel):
    tokens: list[str] = Field(
        default_factory=list,
        description="Vault tokens to resolve (e.g. '<PERSON_a1b2c3d4>').",
    )


class DetokenizeResponse(BaseModel):
    values: dict[str, str] = Field(
        default_factory=dict,
        description="Resolved token → plaintext for the current tenant only.",
    )


__all__ = ["DetokenizeRequest", "DetokenizeResponse"]
