FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATABASE_URL=sqlite:////data/encurtador.db

WORKDIR /srv

# Copiar só o requirements primeiro aproveita o cache de camadas do Docker:
# as dependências só são reinstaladas quando esse arquivo muda.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Roda como usuário comum (sem root) e guarda o banco em um volume.
RUN useradd --create-home appuser && mkdir /data && chown appuser /data
USER appuser
VOLUME /data

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
