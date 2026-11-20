"""API do encurtador de URLs."""

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app import services
from app.database import Base, engine, get_db
from app.models import Link
from app.schemas import LinkCreate, LinkOut


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)  # cria as tabelas se não existirem
    yield


app = FastAPI(title="Encurtador de URLs", version="1.0.0", lifespan=lifespan)


def _para_saida(link: Link, request: Request) -> LinkOut:
    base = str(request.base_url).rstrip("/")
    return LinkOut(
        code=link.code,
        url=link.url,
        short_url=f"{base}/{link.code}",
        clicks=link.clicks,
        created_at=link.created_at,
    )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/links", response_model=LinkOut, status_code=status.HTTP_201_CREATED)
def criar(payload: LinkCreate, request: Request, db: Session = Depends(get_db)):
    try:
        link = services.criar_link(db, str(payload.url), payload.custom_code)
    except services.CodigoInvalido as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(e))
    except services.CodigoEmUso as e:
        raise HTTPException(status.HTTP_409_CONFLICT, str(e))
    return _para_saida(link, request)


@app.get("/links", response_model=list[LinkOut])
def listar(request: Request, db: Session = Depends(get_db)):
    return [_para_saida(link, request) for link in services.listar_links(db)]


@app.get("/links/{code}", response_model=LinkOut)
def estatisticas(code: str, request: Request, db: Session = Depends(get_db)):
    link = services.buscar_link(db, code)
    if link is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Link não encontrado.")
    return _para_saida(link, request)


@app.delete("/links/{code}", status_code=status.HTTP_204_NO_CONTENT)
def apagar(code: str, db: Session = Depends(get_db)):
    if not services.apagar_link(db, code):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Link não encontrado.")


# Esta rota "pega tudo" precisa ficar por último, senão engoliria as de cima.
@app.get("/{code}")
def redirecionar(code: str, db: Session = Depends(get_db)):
    link = services.buscar_link(db, code)
    if link is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Link não encontrado.")
    services.registrar_clique(db, code)
    return RedirectResponse(link.url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
