"""Tabela links original (antes da autenticação)

Revision ID: 0001
Revises:
Create Date: 2026-11-20
"""

from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Bancos criados antes do Alembic (com create_all) já têm a tabela `links`:
    # nesse caso não há nada a fazer, e o Alembic só passa a controlar a versão.
    if sa.inspect(op.get_bind()).has_table("links"):
        return
    op.create_table(
        "links",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("url", sa.String(2048), nullable=False),
        sa.Column("clicks", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_links_code", "links", ["code"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_links_code", table_name="links")
    op.drop_table("links")
