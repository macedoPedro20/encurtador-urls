"""Ambiente do Alembic.

Usa o mesmo engine da aplicação (app.database.engine), a não ser que quem chamou
passe outro em `config.attributes["engine"]` (os testes fazem isso).
"""

from alembic import context

from app.database import Base, engine as engine_da_app
from app import models  # noqa: F401  (registra as tabelas em Base.metadata)

config = context.config
target_metadata = Base.metadata


def run_migrations_online() -> None:
    engine = config.attributes.get("engine") or engine_da_app
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # SQLite quase não suporta ALTER TABLE; o modo "batch" recria a tabela quando precisa.
            render_as_batch=connection.dialect.name == "sqlite",
        )
        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()
