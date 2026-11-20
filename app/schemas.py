"""Schemas Pydantic: validam a entrada e definem o formato das respostas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


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
