"""Add tenant_id to tenant-scoped tables.

Revision ID: 002
Revises: 001
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLES = ("documents", "index_jobs", "chat_sessions", "chat_messages")


def upgrade() -> None:
    for table in TABLES:
        op.add_column(
            table,
            sa.Column(
                "tenant_id",
                sa.String(length=255),
                nullable=False,
                server_default="default",
            ),
        )
        op.create_index(f"ix_{table}_tenant_id", table, ["tenant_id"], unique=False)
        op.alter_column(table, "tenant_id", server_default=None)

    op.drop_constraint("documents_minio_key_key", "documents", type_="unique")
    op.create_unique_constraint(
        "uq_documents_tenant_minio_key",
        "documents",
        ["tenant_id", "minio_key"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_documents_tenant_minio_key", "documents", type_="unique")
    op.create_unique_constraint("documents_minio_key_key", "documents", ["minio_key"])

    for table in reversed(TABLES):
        op.drop_index(f"ix_{table}_tenant_id", table_name=table)
        op.drop_column(table, "tenant_id")
