import logging

from agentic_shared.integrations.keycloak_admin.errors import KeycloakNotFoundError
from agentic_shared.integrations.keycloak_admin.gateway import UserGateway, UserRecord

from agentic_admin.modules.users.schemas import UpdateUserRequest, UserOut

logger = logging.getLogger(__name__)


class UserAdminService:
    def __init__(self, gateway: UserGateway) -> None:
        self._gateway = gateway

    @staticmethod
    def _out(record: UserRecord) -> UserOut:
        return UserOut(
            id=record.id,
            username=record.username,
            email=record.email,
            enabled=record.enabled,
            tenant_id=record.tenant_id,
            tenant_ids=list(record.tenant_ids),
            realm_roles=list(record.realm_roles),
        )

    async def list_users(
        self,
        *,
        search: str | None = None,
        first: int = 0,
        max_results: int = 50,
    ) -> tuple[list[UserOut], bool]:
        records, has_more = await self._gateway.list_users(
            search=search, first=first, max_results=max_results
        )
        items = [self._out(r) for r in records if not r.username.startswith("service-account-")]
        return items, has_more

    async def get_user(self, username: str) -> UserOut:
        record = await self._gateway.get_by_username(username)
        if not record:
            raise KeycloakNotFoundError(f"User not found: {username}")
        return self._out(record)

    async def create_user(
        self,
        *,
        username: str,
        email: str | None,
        password: str,
        realm_roles: list[str],
    ) -> UserOut:
        record = await self._gateway.create_user(
            username=username,
            email=email,
            password=password,
            realm_roles=realm_roles or None,
        )
        logger.info("created user username=%s roles=%s", record.username, record.realm_roles)
        return self._out(record)

    async def assign_tenant(
        self, username: str, tenant_alias: str, *, set_active: bool | None = None
    ) -> UserOut:
        record = await self._gateway.assign_tenant(username, tenant_alias, set_active=set_active)
        logger.info(
            "assigned tenant username=%s tenant=%s set_active=%s",
            username,
            tenant_alias,
            set_active,
        )
        return self._out(record)

    async def set_active_tenant(self, username: str, tenant_alias: str) -> UserOut:
        record = await self._gateway.set_active_tenant(username, tenant_alias)
        logger.info("set active tenant username=%s tenant=%s", username, tenant_alias)
        return self._out(record)

    async def remove_tenant(self, username: str) -> UserOut:
        record = await self._gateway.remove_tenant(username)
        logger.info("cleared tenant username=%s", username)
        return self._out(record)

    async def remove_from_tenant(self, username: str, tenant_alias: str) -> UserOut:
        record = await self._gateway.remove_from_tenant_org(username, tenant_alias)
        logger.info("removed user from tenant username=%s tenant=%s", username, tenant_alias)
        return self._out(record)

    async def update_user(self, username: str, body: UpdateUserRequest) -> UserOut:
        clear_tenant = False
        tenant_alias: str | None = None
        if body.tenant_id is not None:
            if body.tenant_id == "":
                clear_tenant = True
            else:
                tenant_alias = body.tenant_id

        record = await self._gateway.update_user(
            username,
            email=body.email,
            enabled=body.enabled,
            realm_roles=body.realm_roles,
            tenant_alias=tenant_alias,
            clear_tenant=clear_tenant,
            password=body.password,
        )
        logger.info("updated user username=%s enabled=%s", username, body.enabled)
        return self._out(record)
