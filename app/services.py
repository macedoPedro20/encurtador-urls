"""Regras de negócio: gerar códigos, criar e buscar links."""

import re
import secrets
import string

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import security
from app.models import Link, User

ALFABETO = string.ascii_letters + string.digits  # base62
TAMANHO_CODIGO = 6
MAX_TENTATIVAS = 10
CODIGO_VALIDO = re.compile(r"^[A-Za-z0-9_-]{3,32}$")
# Rotas da própria API não podem ser usadas como código curto.
CODIGOS_RESERVADOS = {"links", "auth", "docs", "redoc", "openapi.json", "health"}


class CodigoInvalido(Exception):
    pass


class CodigoEmUso(Exception):
    pass


class EmailEmUso(Exception):
    pass


def gerar_codigo() -> str:
    # `secrets` (e não `random`) para que os códigos não sejam previsíveis.
    return "".join(secrets.choice(ALFABETO) for _ in range(TAMANHO_CODIGO))


def criar_link(
    db: Session, url: str, custom_code: str | None = None, owner_id: int | None = None
) -> Link:
    if custom_code is not None:
        if not CODIGO_VALIDO.match(custom_code) or custom_code.lower() in CODIGOS_RESERVADOS:
            raise CodigoInvalido("Código inválido ou reservado.")
        return _salvar(db, url, custom_code, owner_id, erro=CodigoEmUso("Esse código já está em uso."))

    # Código aleatório: em caso (raro) de colisão, tenta de novo.
    for _ in range(MAX_TENTATIVAS):
        try:
            return _salvar(db, url, gerar_codigo(), owner_id, erro=None)
        except IntegrityError:
            continue
    raise RuntimeError("Não foi possível gerar um código único.")


def _salvar(db: Session, url: str, code: str, owner_id: int | None, erro: Exception | None) -> Link:
    link = Link(code=code, url=url, owner_id=owner_id)
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


def listar_links(db: Session, owner_id: int, limite: int = 50) -> list[Link]:
    consulta = (
        select(Link)
        .where(Link.owner_id == owner_id)
        .order_by(Link.created_at.desc(), Link.id.desc())
        .limit(limite)
    )
    return list(db.scalars(consulta))


def apagar_link(db: Session, code: str, owner_id: int) -> bool:
    """Apaga o link se ele existir E pertencer ao usuário.

    Link de outra pessoa se comporta como inexistente (404), para não revelar
    quais códigos existem.
    """
    link = buscar_link(db, code)
    if link is None or link.owner_id != owner_id:
        return False
    db.delete(link)
    db.commit()
    return True


def criar_usuario(db: Session, email: str, senha: str) -> User:
    usuario = User(email=email, password_hash=security.hash_senha(senha))
    db.add(usuario)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise EmailEmUso("Já existe uma conta com esse e-mail.")
    return usuario


def autenticar(db: Session, email: str, senha: str) -> User | None:
    usuario = db.scalar(select(User).where(User.email == email))
    # Sempre verifica uma senha (mesmo sem usuário) para o tempo de resposta ser igual.
    senha_ok = security.verificar_senha(senha, usuario.password_hash if usuario else None)
    return usuario if usuario and senha_ok else None


def buscar_usuario(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)
