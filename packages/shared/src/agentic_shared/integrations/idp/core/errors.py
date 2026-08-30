class IdpError(Exception):
    """Identity-provider admin operation failed."""


class IdpConflictError(IdpError):
    pass


class IdpNotFoundError(IdpError):
    pass


class IdpForbiddenError(IdpError):
    pass
