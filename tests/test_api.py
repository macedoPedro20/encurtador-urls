import pytest


def test_pagina_inicial_e_servida(client):
    r = client.get("/")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/html")
    assert "Encurtador de URLs" in r.text


def test_criar_link_gera_codigo_curto(client):
    r = client.post("/links", json={"url": "https://example.com/uma/pagina/longa"})
    assert r.status_code == 201
    corpo = r.json()
    assert len(corpo["code"]) == 6
    assert corpo["short_url"].endswith("/" + corpo["code"])
    assert corpo["clicks"] == 0


def test_created_at_tem_fuso_horario_consistente(client):
    criado = client.post("/links", json={"url": "https://example.com"}).json()
    consultado = client.get(f"/links/{criado['code']}").json()

    # Antes o SQLite devolvia a data sem fuso ("...Z" só na criação).
    assert criado["created_at"].endswith("Z")
    assert consultado["created_at"] == criado["created_at"]


def test_url_invalida_retorna_422(client):
    r = client.post("/links", json={"url": "isso-nao-e-uma-url"})
    assert r.status_code == 422


def test_esquema_perigoso_e_rejeitado(client):
    r = client.post("/links", json={"url": "javascript:alert(1)"})
    assert r.status_code == 422


def test_redireciona_e_conta_cliques(client):
    code = client.post("/links", json={"url": "https://example.com"}).json()["code"]

    for _ in range(3):
        r = client.get(f"/{code}", follow_redirects=False)
        assert r.status_code == 307
        assert r.headers["location"] == "https://example.com/"

    stats = client.get(f"/links/{code}").json()
    assert stats["clicks"] == 3


def test_codigo_inexistente_retorna_404(client):
    assert client.get("/naoexiste", follow_redirects=False).status_code == 404
    assert client.get("/links/naoexiste").status_code == 404


def test_codigo_personalizado(client):
    r = client.post("/links", json={"url": "https://example.com", "custom_code": "meu-site"})
    assert r.status_code == 201
    assert r.json()["code"] == "meu-site"


def test_codigo_personalizado_duplicado_retorna_409(client):
    payload = {"url": "https://example.com", "custom_code": "meu-site"}
    assert client.post("/links", json=payload).status_code == 201
    assert client.post("/links", json=payload).status_code == 409


@pytest.mark.parametrize("codigo", ["links", "docs", "a b c", "ab"])
def test_codigo_personalizado_invalido_ou_reservado(client, codigo):
    r = client.post("/links", json={"url": "https://example.com", "custom_code": codigo})
    assert r.status_code == 422


def test_listar_e_apagar_com_login(client, login):
    headers = login("ana@example.com")
    code = client.post("/links", json={"url": "https://example.com"}, headers=headers).json()["code"]
    assert [l["code"] for l in client.get("/links", headers=headers).json()] == [code]

    assert client.delete(f"/links/{code}", headers=headers).status_code == 204
    assert client.get("/links", headers=headers).json() == []
    assert client.delete(f"/links/{code}", headers=headers).status_code == 404
