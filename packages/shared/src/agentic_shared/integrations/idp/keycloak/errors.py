from agentic_shared.integrations.idp.core.errors import (
    IdpConflictError,
    IdpError,
    IdpForbiddenError,
    IdpNotFoundError,
)


class KeycloakAdminError(IdpError):
    """Keycloak Admin REST call failed."""


class KeycloakConflictError(KeycloakAdminError, IdpConflictError):
    pass


class KeycloakNotFoundError(KeycloakAdminError, IdpNotFoundError):
    pass


class KeycloakForbiddenError(KeycloakAdminError, IdpForbiddenError):
    pass
