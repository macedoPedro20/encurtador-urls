"""Cadastro, login e dependências de autenticação."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import security, services
from app.database import get_db
from app.models import User
from app.schemas import TokenOut, UserCreate, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])

# auto_error=False: quem decide se o token é obrigatório são as dependências abaixo.
# O tokenUrl faz o botão "Authorize" do Swagger (/docs) funcionar.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

_NAO_AUTORIZADO = HTTPException(
    status.HTTP_401_UNAUTHORIZED,
    "Credenciais ausentes, inválidas ou expiradas.",
    headers={"WWW-Authenticate": "Bearer"},
)


def usuario_opcional(
    token: str | None = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User | None:
    """Sem token: anônimo (None). Com token inválido/expirado: 401, nunca anônimo."""
    if token is None:
        return None
    user_id = security.ler_token(token)
    usuario = services.buscar_usuario(db, user_id) if user_id is not None else None
    if usuario is None:
        raise _NAO_AUTORIZADO
    return usuario


def usuario_atual(usuario: User | None = Depends(usuario_opcional)) -> User:
    if usuario is None:
        raise _NAO_AUTORIZADO
    return usuario


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def cadastrar(payload: UserCreate, db: Session = Depends(get_db)):
    try:
        return services.criar_usuario(db, payload.email, payload.password)
    except services.EmailEmUso as e:
        raise HTTPException(status.HTTP_409_CONFLICT, str(e))


@router.post("/login", response_model=TokenOut)
def entrar(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # O formulário OAuth2 chama o e-mail de "username".
    usuario = services.autenticar(db, form.username.strip().lower(), form.password)
    if usuario is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "E-mail ou senha incorretos.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TokenOut(access_token=security.criar_token(usuario.id))


@router.get("/me", response_model=UserOut)
def eu(usuario: User = Depends(usuario_atual)):
    return usuario
