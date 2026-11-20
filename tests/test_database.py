import pytest

from app.database import normalizar_url_banco


@pytest.mark.parametrize(
    "entrada, esperado",
    [
        ("postgres://u:p@host:5432/db", "postgresql+psycopg://u:p@host:5432/db"),
        ("postgresql://u:p@host/db", "postgresql+psycopg://u:p@host/db"),
        ("postgresql+psycopg://u:p@host/db", "postgresql+psycopg://u:p@host/db"),
        ("sqlite:///./encurtador.db", "sqlite:///./encurtador.db"),
    ],
)
def test_normalizar_url_banco(entrada, esperado):
    assert normalizar_url_banco(entrada) == esperado
