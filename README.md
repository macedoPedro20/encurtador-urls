# Encurtador de URLs

API REST para encurtar links, feita com **Python, FastAPI e SQLite**. Transforma uma URL longa em um código curto (ex.: `http://localhost:8000/aB3xY9`), redireciona quem acessa e conta os cliques.

**Demo online:** https://encurtador-urls-r1rj.onrender.com/docs

> Roda no plano gratuito da Render: se a demo estiver parada, a primeira visita pode demorar cerca de um minuto para "acordar". Os links criados na demo são apagados quando o serviço reinicia.

## Funcionalidades

- Encurtar URLs com código aleatório (base62, gerado com `secrets`) ou **personalizado**
- Redirecionamento HTTP 307 com **contagem de cliques** atômica
- Validação de entrada (só `http`/`https`; rejeita `javascript:` e similares)
- Tratamento de colisão de códigos e de códigos reservados
- Listagem, consulta de estatísticas e remoção de links
- Documentação interativa automática (Swagger) em `/docs`
- Testes automatizados com banco em memória

## Como rodar

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

uvicorn app.main:app --reload
```

Abra http://localhost:8000/docs para testar pela interface do Swagger.

### Com Docker

```bash
docker build -t encurtador-urls .
docker run -p 8000:8000 -v encurtador-data:/data encurtador-urls
```

O volume `encurtador-data` guarda o banco SQLite, então os links sobrevivem a reinicializações do container.

## Endpoints

| Método | Rota             | Descrição                                   |
|--------|------------------|---------------------------------------------|
| POST   | `/links`         | Cria um link curto (`url`, `custom_code?`)  |
| GET    | `/links`         | Lista os links mais recentes                |
| GET    | `/links/{code}`  | Estatísticas de um link                     |
| DELETE | `/links/{code}`  | Remove um link                              |
| GET    | `/{code}`        | Redireciona para a URL original             |
| GET    | `/health`        | Verifica se a API está no ar                |

Exemplo:

```bash
curl -X POST http://localhost:8000/links \
  -H "Content-Type: application/json" \
  -d '{"url": "https://github.com", "custom_code": "meu-github"}'
```

## Testes

```bash
pytest
```

A cada push e pull request, o GitHub Actions roda os testes em Python 3.12 e 3.13 (`.github/workflows/ci.yml`).

## Deploy (Render)

O repositório inclui um `render.yaml` (Blueprint). Para publicar:

1. Na [Render](https://render.com), escolha **New → Blueprint** e conecte este repositório.
2. A Render lê o `render.yaml`, constrói a imagem do `Dockerfile` e sobe o serviço.
3. Cada push na `main` gera um novo deploy automaticamente.

> **Atenção:** no plano gratuito o disco é efêmero e o serviço "dorme" após alguns minutos sem uso. Por isso o banco SQLite é reiniciado a cada novo deploy ou reinício, e o primeiro acesso depois de um tempo parado pode demorar. Para persistência de verdade, o próximo passo é trocar o SQLite por PostgreSQL.

## Estrutura

```
app/
  main.py       # rotas HTTP
  services.py   # regras de negócio (gerar código, clicar, apagar)
  models.py     # tabela do banco (SQLAlchemy)
  schemas.py    # validação e formato das respostas (Pydantic)
  database.py   # conexão com o banco
tests/
  test_api.py
```

## Decisões de projeto

- **`secrets` em vez de `random`**: códigos não previsíveis.
- **`UPDATE clicks = clicks + 1` no banco**: evita perder cliques em acessos simultâneos.
- **307 em vez de 301**: o navegador não faz cache do redirecionamento, então os cliques continuam sendo contados.
- **Camada de serviço separada das rotas**: facilita testar e trocar o banco depois.

## Próximos passos

- [ ] Expiração de links
- [ ] Autenticação e links por usuário
- [x] Dockerfile
- [x] GitHub Actions rodando os testes
- [x] Configuração de deploy (Render)
- [x] Link da demo online neste README
- [ ] Trocar SQLite por PostgreSQL (persistência)
