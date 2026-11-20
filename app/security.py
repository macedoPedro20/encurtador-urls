"""Senhas (hash Argon2) e tokens JWT."""

import logging
import os
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

logger = logging.getLogger(__name__)

ALGORITMO = "HS256"
MINUTOS_DE_VALIDADE = int(os.getenv("ACCESS_TOKEN_MINUTES", "60"))

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    # Em desenvolvimento dá para seguir sem configurar nada, mas os tokens deixam
    # de valer a cada reinício. Em produção, defina SECRET_KEY (ver README).
    SECRET_KEY = secrets.token_urlsafe(32)
    logger.warning("SECRET_KEY não definida: usando uma chave temporária (os logins expiram ao reiniciar).")

_hasher = PasswordHash.recommended()  # Argon2id
# Hash "de mentira" usado quando o e-mail não existe: o login leva o mesmo tempo
# com e-mail inexistente ou senha errada, e não revela quais e-mails têm conta.
_HASH_FALSO = _hasher.hash("senha-falsa-para-igualar-o-tempo")


def hash_senha(senha: str) -> str:
    return _hasher.hash(senha)


def verificar_senha(senha: str, hash_guardado: str | None) -> bool:
    return _hasher.verify(senha, hash_guardado or _HASH_FALSO) and hash_guardado is not None


def criar_token(user_id: int) -> str:
    agora = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": agora,
        "exp": agora + timedelta(minutes=MINUTOS_DE_VALIDADE),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITMO)


def ler_token(token: str) -> int | None:
    """Devolve o id do usuário se o token for válido e não tiver expirado."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITMO], options={"require": ["exp", "sub"]})
        return int(payload["sub"])
    except (jwt.PyJWTError, ValueError):
        return None
