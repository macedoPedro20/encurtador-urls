from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app import security

SENHA_PADRAO = "senha-segura-123"


def _registrar(client, email="ana@example.com", senha=SENHA_PADRAO):
    return client.post("/auth/register", json={"email": email, "password": senha})


def test_cadastro_devolve_usuario_sem_senha(client):
    r = _registrar(client, "  Ana@Example.com ")
    assert r.status_code == 201
    corpo = r.json()
    assert corpo["email"] == "ana@example.com"  # normalizado
    assert "password" not in corpo and "password_hash" not in corpo


def test_cadastro_com_email_repetido_retorna_409(client):
    assert _registrar(client).status_code == 201
    assert _registrar(client, "ANA@example.com").status_code == 409


@pytest.mark.parametrize(
    "email, senha",
    [("sem-arroba", SENHA_PADRAO), ("a@b", SENHA_PADRAO), ("ana@example.com", "curta")],
)
def test_cadastro_invalido_retorna_422(client, email, senha):
    assert _registrar(client, email, senha).status_code == 422


def test_senha_e_guardada_com_hash(client):
    from app.main import app
    from app.database import get_db
    from app.models import User

    _registrar(client)
    db = next(app.dependency_overrides[get_db]())
    usuario = db.query(User).one()
    assert usuario.password_hash != SENHA_PADRAO
    assert usuario.password_hash.startswith("$argon2")
    db.close()


def test_login_correto_devolve_token(client):
    _registrar(client)
    r = client.post("/auth/login", data={"username": "ana@example.com", "password": SENHA_PADRAO})
    assert r.status_code == 200
    assert r.json()["token_type"] == "bearer"
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {r.json()['access_token']}"}).json()[
        "email"
    ] == "ana@example.com"


def test_login_com_senha_errada_ou_email_inexistente_tem_a_mesma_resposta(client):
    _registrar(client)
    errada = client.post("/auth/login", data={"username": "ana@example.com", "password": "outra-senha-123"})
    inexistente = client.post("/auth/login", data={"username": "fulano@example.com", "password": SENHA_PADRAO})
    assert errada.status_code == inexistente.status_code == 401
    assert errada.json() == inexistente.json()


def test_rotas_protegidas_exigem_token(client):
    assert client.get("/links").status_code == 401
    assert client.delete("/links/abc").status_code == 401
    assert client.get("/auth/me").status_code == 401


def test_token_invalido_e_rejeitado_mesmo_ao_criar_link(client):
    # Token ruim não pode virar "anônimo" em silêncio.
    r = client.post(
        "/links", json={"url": "https://example.com"}, headers={"Authorization": "Bearer lixo"}
    )
    assert r.status_code == 401


def test_token_expirado_e_rejeitado(client):
    _registrar(client)
    passado = datetime.now(timezone.utc) - timedelta(hours=1)
    token = jwt.encode({"sub": "1", "exp": passado}, security.SECRET_KEY, algorithm=security.ALGORITMO)
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 401


def test_token_assinado_com_outra_chave_e_rejeitado(client):
    _registrar(client)
    futuro = datetime.now(timezone.utc) + timedelta(hours=1)
    token = jwt.encode({"sub": "1", "exp": futuro}, "chave-errada-" * 4, algorithm=security.ALGORITMO)
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 401


def test_link_anonimo_continua_funcionando_mas_nao_aparece_para_ninguem(client, login):
    code = client.post("/links", json={"url": "https://example.com"}).json()["code"]
    headers = login("ana@example.com")

    assert client.get(f"/{code}", follow_redirects=False).status_code == 307
    assert client.get(f"/links/{code}").status_code == 200
    assert client.get("/links", headers=headers).json() == []
    # ...e ninguém consegue apagar um link anônimo pela API.
    assert client.delete(f"/links/{code}", headers=headers).status_code == 404


def test_cada_usuario_ve_e_apaga_apenas_os_proprios_links(client, login):
    ana = login("ana@example.com")
    bia = login("bia@example.com")
    code_ana = client.post("/links", json={"url": "https://example.com/ana"}, headers=ana).json()["code"]
    code_bia = client.post("/links", json={"url": "https://example.com/bia"}, headers=bia).json()["code"]

    assert [l["code"] for l in client.get("/links", headers=ana).json()] == [code_ana]
    assert [l["code"] for l in client.get("/links", headers=bia).json()] == [code_bia]

    # Bia não consegue apagar o link da Ana (404, como se não existisse)...
    assert client.delete(f"/links/{code_ana}", headers=bia).status_code == 404
    assert client.get(f"/links/{code_ana}").status_code == 200
    # ...mas a Ana consegue.
    assert client.delete(f"/links/{code_ana}", headers=ana).status_code == 204


def test_auth_e_codigo_reservado(client):
    r = client.post("/links", json={"url": "https://example.com", "custom_code": "auth"})
    assert r.status_code == 422
