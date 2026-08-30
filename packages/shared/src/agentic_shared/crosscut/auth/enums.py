from enum import StrEnum


class AuthMode(StrEnum):
    NONE = "none"
    API_KEY = "api_key"
    JWT = "jwt"
