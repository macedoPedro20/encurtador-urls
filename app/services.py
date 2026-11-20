"""Regras de negócio: gerar códigos, criar e buscar links."""

import re
import secrets
import string

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Link

ALFABETO = string.ascii_letters + string.digits  # base62
TAMANHO_CODIGO = 6
MAX_TENTATIVAS = 10
CODIGO_VALIDO = re.compile(r"^[A-Za-z0-9_-]{3,32}$")
# Rotas da própria API não podem ser usadas como código curto.
CODIGOS_RESERVADOS = {"links", "docs", "redoc", "openapi.json", "health"}


class CodigoInvalido(Exception):
    pass


class CodigoEmUso(Exception):
    pass


def gerar_codigo() -> str:
    # `secrets` (e não `random`) para que os códigos não sejam previsíveis.
    return "".join(secrets.choice(ALFABETO) for _ in range(TAMANHO_CODIGO))


def criar_link(db: Session, url: str, custom_code: str | None = None) -> Link:
    if custom_code is not None:
        if not CODIGO_VALIDO.match(custom_code) or custom_code.lower() in CODIGOS_RESERVADOS:
            raise CodigoInvalido("Código inválido ou reservado.")
        return _salvar(db, url, custom_code, erro=CodigoEmUso("Esse código já está em uso."))

    # Código aleatório: em caso (raro) de colisão, tenta de novo.
    for _ in range(MAX_TENTATIVAS):
        try:
            return _salvar(db, url, gerar_codigo(), erro=None)
        except IntegrityError:
            continue
    raise RuntimeError("Não foi possível gerar um código único.")


def _salvar(db: Session, url: str, code: str, erro: Exception | None) -> Link:
    link = Link(code=code, url=url)
    db.add(link)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        if erro is not None:
            raise erro
        raise
    return link


def buscar_link(db: Session, code: str) -> Link | None:
    return db.scalar(select(Link).where(Link.code == code))


def registrar_clique(db: Session, code: str) -> None:
    # UPDATE atômico no banco evita perder cliques em requisições simultâneas
    # (ao contrário de ler, somar 1 em Python e salvar).
    db.execute(update(Link).where(Link.code == code).values(clicks=Link.clicks + 1))
    db.commit()


def listar_links(db: Session, limite: int = 50) -> list[Link]:
    return list(db.scalars(select(Link).order_by(Link.created_at.desc()).limit(limite)))


def apagar_link(db: Session, code: str) -> bool:
    link = buscar_link(db, code)
    if link is None:
        return False
    db.delete(link)
    db.commit()
    return True
