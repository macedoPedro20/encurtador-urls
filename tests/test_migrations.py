"""Garante que as migrações (Alembic) e os modelos (SQLAlchemy) contam a mesma história."""

from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, inspect, text

from app.database import Base
from app.migrate import aplicar_migracoes


def _engine(tmp_path):
    return create_engine(f"sqlite:///{tmp_path / 'banco.db'}")


def test_migracoes_criam_o_esquema_dos_modelos(tmp_path):
    engine = _engine(tmp_path)
    aplicar_migracoes(engine)

    tabelas = set(inspect(engine).get_table_names())
    assert {"links", "users", "alembic_version"} <= tabelas

    # Se alguém mudar um modelo e esquecer a migração, este teste acusa a diferença.
    with engine.connect() as conn:
        diferencas = compare_metadata(MigrationContext.configure(conn), Base.metadata)
    assert diferencas == []


def test_migracoes_sao_idempotentes(tmp_path):
    engine = _engine(tmp_path)
    aplicar_migracoes(engine)
    aplicar_migracoes(engine)  # rodar de novo não pode falhar nem duplicar nada


def test_banco_antigo_sem_alembic_e_atualizado_sem_perder_links(tmp_path):
    """Simula o banco de produção criado antes da autenticação (via create_all, sem Alembic)."""
    engine = _engine(tmp_path)
    with engine.begin() as conn:
        conn.execute(text(
            "CREATE TABLE links (id INTEGER PRIMARY KEY, code VARCHAR(32) NOT NULL, "
            "url VARCHAR(2048) NOT NULL, clicks INTEGER NOT NULL, created_at DATETIME NOT NULL)"
        ))
        conn.execute(text("CREATE UNIQUE INDEX ix_links_code ON links (code)"))
        conn.execute(text(
            "INSERT INTO links (code, url, clicks, created_at) "
            "VALUES ('antigo', 'https://example.com/', 7, '2026-01-01 00:00:00')"
        ))

    aplicar_migracoes(engine)

    colunas = {c["name"] for c in inspect(engine).get_columns("links")}
    assert "owner_id" in colunas
    with engine.connect() as conn:
        linha = conn.execute(text("SELECT code, clicks, owner_id FROM links")).one()
    assert tuple(linha) == ("antigo", 7, None)  # preservado, e anônimo
