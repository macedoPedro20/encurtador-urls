# Encurtador de URLs

API REST para encurtar links, feita com **Python, FastAPI e SQLite**. Transforma uma URL longa em um código curto (ex.: `http://localhost:8000/aB3xY9`), redireciona quem acessa e conta os cliques.

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
pip install -r requirements.txt

uvicorn app.main:app --reload
```

Abra http://localhost:8000/docs para testar pela interface do Swagger.

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
- [ ] Dockerfile + deploy
- [ ] GitHub Actions rodando os testes
