"""Re-export IdP records (Keycloak adapter uses the shared models)."""

from agentic_shared.integrations.idp.core.records import UserRecord

__all__ = ["UserRecord"]
