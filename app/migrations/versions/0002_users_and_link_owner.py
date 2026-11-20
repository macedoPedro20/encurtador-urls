"""Usuários e dono dos links

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-20
"""

from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(254), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # Links já existentes ficam com owner_id nulo (anônimos).
    with op.batch_alter_table("links") as batch:
        batch.add_column(sa.Column("owner_id", sa.Integer(), nullable=True))
        batch.create_foreign_key("fk_links_owner_id_users", "users", ["owner_id"], ["id"], ondelete="CASCADE")
        batch.create_index("ix_links_owner_id", ["owner_id"])


def downgrade() -> None:
    with op.batch_alter_table("links") as batch:
        batch.drop_index("ix_links_owner_id")
        batch.drop_constraint("fk_links_owner_id_users", type_="foreignkey")
        batch.drop_column("owner_id")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
