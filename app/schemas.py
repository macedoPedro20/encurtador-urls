"""Schemas Pydantic: validam a entrada e definem o formato das respostas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class LinkCreate(BaseModel):
    url: HttpUrl
    # Código personalizado opcional (ex.: "meu-portfolio"). Validado no serviço.
    custom_code: str | None = Field(default=None, min_length=3, max_length=32)


class LinkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    url: str
    short_url: str
    clicks: int
    created_at: datetime


class UserCreate(BaseModel):
    email: str = Field(max_length=254, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(min_length=8, max_length=128)

    # mode="before": normaliza ANTES de validar o formato (senão o espaço reprovaria).
    @field_validator("email", mode="before")
    @classmethod
    def normalizar_email(cls, valor):
        return valor.strip().lower() if isinstance(valor, str) else valor


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
