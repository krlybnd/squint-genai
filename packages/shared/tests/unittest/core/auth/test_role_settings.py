from agentic_shared.core.auth.roles import AppRole
from agentic_shared.core.auth.settings import RoleSettings


def test_role_settings_parses_loose_bash_sourced_roles() -> None:
    settings = RoleSettings.model_validate({"roles": "{admin:admin,read:read,write:write}"})

    assert settings.roles["admin"] is AppRole.ADMIN
    assert settings.roles["read"] is AppRole.READ
    assert settings.roles["write"] is AppRole.WRITE
