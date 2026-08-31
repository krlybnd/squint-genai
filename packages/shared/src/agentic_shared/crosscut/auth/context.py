from dataclasses import dataclass, field

from agentic_shared.crosscut.auth.roles import AppRole


@dataclass(frozen=True, slots=True)
class AuthContext:
    user_id: str | None
    tenant_id: str | None
    roles: frozenset[AppRole] = field(default_factory=frozenset)
    username: str | None = None

    @classmethod
    def anonymous(cls) -> "AuthContext":
        return cls(user_id=None, tenant_id=None, roles=frozenset(AppRole.privileged()))

    def has_role(self, role: AppRole) -> bool:
        if AppRole.ADMIN in self.roles:
            return True
        return role in self.roles

    def has_any(self, *roles: AppRole) -> bool:
        return any(self.has_role(role) for role in roles)
