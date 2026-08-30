from enum import StrEnum


class AppRole(StrEnum):
    """Application RBAC roles — mapped from Keycloak realm roles via settings."""

    ADMIN = "admin"
    READ = "read"
    WRITE = "write"

    @classmethod
    def privileged(cls) -> frozenset["AppRole"]:
        return frozenset({cls.ADMIN, cls.READ, cls.WRITE})
