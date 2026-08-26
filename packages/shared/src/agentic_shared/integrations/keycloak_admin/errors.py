class KeycloakAdminError(Exception):
    """Keycloak Admin REST call failed."""


class KeycloakConflictError(KeycloakAdminError):
    pass


class KeycloakNotFoundError(KeycloakAdminError):
    pass


class KeycloakForbiddenError(KeycloakAdminError):
    pass
