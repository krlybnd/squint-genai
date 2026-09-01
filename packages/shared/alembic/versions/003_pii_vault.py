"""Add pii_vault_entries for index-time PII tokenization.

Revision ID: 003
Revises: 002
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: str | None = "002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "pii_vault_entries",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.String(length=255), nullable=False),
        sa.Column("token", sa.String(length=64), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("ciphertext", sa.Text(), nullable=False),
        sa.Column("first_doc_id", sa.UUID(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "token", name="uq_pii_vault_tenant_token"),
    )
    op.create_index(
        "ix_pii_vault_entries_tenant_id",
        "pii_vault_entries",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        "ix_pii_vault_entries_token",
        "pii_vault_entries",
        ["token"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_pii_vault_entries_token", table_name="pii_vault_entries")
    op.drop_index("ix_pii_vault_entries_tenant_id", table_name="pii_vault_entries")
    op.drop_table("pii_vault_entries")
