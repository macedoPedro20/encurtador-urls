"""Aplica as migrações do banco (Alembic) programaticamente."""

from pathlib import Path

from alembic import command
from alembic.config import Config

PASTA_MIGRACOES = Path(__file__).parent / "migrations"


def aplicar_migracoes(engine=None) -> None:
    """Leva o banco até a versão mais recente (`alembic upgrade head`)."""
    config = Config()
    config.set_main_option("script_location", str(PASTA_MIGRACOES))
    if engine is not None:
        config.attributes["engine"] = engine
    command.upgrade(config, "head")
