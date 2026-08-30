"""Settings for SecurityHeadersMiddleware."""

from pydantic import Field
from pydantic_settings import SettingsConfigDict

from agentic_shared.frameworks.core.settings import FrameworkSettings


class SecurityHeadersSettings(FrameworkSettings):
    """Env-tunable response security headers (CSP, frame options, …)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        env_prefix="SECURITY_HEADERS_",
    )

    title: str = Field(
        default="security_headers",
        description="Log label for this settings slice.",
    )
    enabled: bool = Field(
        default=True,
        description="Install SecurityHeadersMiddleware when True.",
    )
    x_content_type_options: str = Field(
        default="nosniff",
        description="X-Content-Type-Options response header value.",
    )
    x_frame_options: str = Field(
        default="DENY",
        description="X-Frame-Options response header value.",
    )
    referrer_policy: str = Field(
        default="strict-origin-when-cross-origin",
        description="Referrer-Policy response header value.",
    )
    x_xss_protection: str = Field(
        default="1; mode=block",
        description="X-XSS-Protection response header value.",
    )
    content_security_policy: str = Field(
        default=(
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "connect-src 'self' http: https: ws: wss:; "
            "img-src 'self' data:; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        ),
        description="Content-Security-Policy response header value.",
    )

    def as_headers(self) -> dict[str, str]:
        return {
            "X-Content-Type-Options": self.x_content_type_options,
            "X-Frame-Options": self.x_frame_options,
            "Referrer-Policy": self.referrer_policy,
            "X-XSS-Protection": self.x_xss_protection,
            "Content-Security-Policy": self.content_security_policy,
        }
