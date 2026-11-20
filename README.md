# Encurtador de URLs

API REST para encurtar links, feita com **Python, FastAPI e SQLAlchemy** (SQLite localmente, PostgreSQL em produção). Transforma uma URL longa em um código curto (ex.: `http://localhost:8000/aB3xY9`), redireciona quem acessa e conta os cliques.

**Demo online:** https://encurtador-urls-r1rj.onrender.com

> Roda no plano gratuito da Render: se a demo estiver parada, a primeira visita pode demorar cerca de um minuto para "acordar". É uma demo: o banco gratuito da Render expira após 30 dias, então os dados podem ser apagados.

## Funcionalidades

- Encurtar URLs com código aleatório (base62, gerado com `secrets`) ou **personalizado**
- Redirecionamento HTTP 307 com **contagem de cliques** atômica
- Validação de entrada (só `http`/`https`; rejeita `javascript:` e similares)
- Tratamento de colisão de códigos e de códigos reservados
- **Contas de usuário**: cadastro e login com senha em hash **Argon2** e token **JWT**
- Links **por usuário**: cada pessoa lista e apaga apenas os próprios links (criar e usar links continua aberto a visitantes)
- Consulta de estatísticas de um link
- **Interface web** em `/`: formulário para encurtar, botão de copiar, login e lista dos seus links com cliques
- **Migrações de banco** com Alembic, aplicadas automaticamente ao iniciar
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

### Com Docker Compose (API + PostgreSQL)

```bash
docker compose up --build
```

Sobe a API em http://localhost:8000 junto com um PostgreSQL. Os dados ficam no volume `pgdata`. Para apagar tudo, incluindo os dados: `docker compose down -v`.

A API escolhe o banco pela variável `DATABASE_URL`. Sem ela, usa SQLite (`encurtador.db`); com uma URL `postgresql://...`, usa PostgreSQL.

### Variáveis de ambiente

| Variável               | Para que serve                                                                 | Padrão                    |
|------------------------|--------------------------------------------------------------------------------|---------------------------|
| `DATABASE_URL`         | Banco de dados (`sqlite:///...` ou `postgresql://...`)                         | `sqlite:///./encurtador.db` |
| `SECRET_KEY`           | Chave que assina os tokens de login. **Obrigatória em produção**, secreta e aleatória (ex.: `python -c "import secrets; print(secrets.token_urlsafe(32))"`) | gerada a cada execução (os logins expiram ao reiniciar) |
| `ACCESS_TOKEN_MINUTES` | Validade do token de login                                                     | `60`                      |
| `AUTO_MIGRATE`         | `0` desliga as migrações automáticas ao iniciar                                | ligado                    |

## Endpoints

| Método | Rota             | Acesso   | Descrição                                          |
|--------|------------------|----------|----------------------------------------------------|
| POST   | `/auth/register` | público  | Cria uma conta (`email`, `password` com 8+ chars)  |
| POST   | `/auth/login`    | público  | Devolve o token (formulário OAuth2: `username` = e-mail) |
| GET    | `/auth/me`       | login    | Dados do usuário logado                            |
| POST   | `/links`         | público  | Cria um link (`url`, `custom_code?`). Com token, o link fica na sua conta |
| GET    | `/links`         | login    | Lista **os seus** links                            |
| GET    | `/links/{code}`  | público  | Estatísticas de um link                            |
| DELETE | `/links/{code}`  | login    | Remove um link **seu**                             |
| GET    | `/{code}`        | público  | Redireciona para a URL original                    |
| GET    | `/`              | público  | Interface web (página única)                       |
| GET    | `/health`        | público  | Verifica se a API está no ar                       |

Exemplo (o botão **Authorize** do Swagger em `/docs` faz o login para você):

```bash
# criar conta e entrar
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "voce@exemplo.com", "password": "uma-senha-longa"}'

TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -d "username=voce@exemplo.com&password=uma-senha-longa" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# criar um link na sua conta e listar os seus
curl -X POST http://localhost:8000/links \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"url": "https://github.com", "custom_code": "meu-github"}'

curl http://localhost:8000/links -H "Authorization: Bearer $TOKEN"
```

## Testes

```bash
pytest
```

Por padrão os testes usam SQLite em memória. Para rodá-los contra um PostgreSQL (descartável, pois as tabelas são criadas e apagadas a cada teste), defina `TEST_DATABASE_URL`:

```bash
TEST_DATABASE_URL=postgresql://usuario:senha@localhost:5432/teste pytest
```

A cada push e pull request, o GitHub Actions roda os testes em Python 3.12 e 3.13 com SQLite, e também em um job separado com um serviço PostgreSQL (`.github/workflows/ci.yml`).

## Migrações de banco (Alembic)

O esquema do banco é versionado em `app/migrations/versions/` e aplicado sozinho ao iniciar a API. Bancos criados antes do Alembic (sem a tabela `alembic_version`) são atualizados sem perder dados. Para mudar o esquema:

```bash
# 1. altere os modelos em app/models.py
# 2. gere a migração e revise o arquivo criado
alembic revision --autogenerate -m "descreva a mudança"
# 3. aplique (ou apenas reinicie a API)
alembic upgrade head
```

Um teste (`tests/test_migrations.py`) falha se os modelos e as migrações ficarem diferentes.

## Deploy (Render)

O repositório inclui um `render.yaml` (Blueprint). Para publicar:

1. Na [Render](https://render.com), escolha **New → Blueprint** e conecte este repositório.
2. A Render lê o `render.yaml`, constrói a imagem do `Dockerfile` e sobe o serviço.
3. Cada push na `main` gera um novo deploy automaticamente.

O Blueprint também cria um banco **PostgreSQL** (`encurtador-db`) e injeta a conexão interna na variável `DATABASE_URL` do serviço, então os links persistem entre deploys. A variável `SECRET_KEY` (que assina os logins) é gerada automaticamente pela Render.

> **Atenção (plano gratuito):** o serviço "dorme" após alguns minutos sem uso, e o primeiro acesso depois disso pode demorar. O PostgreSQL gratuito da Render **expira após 30 dias** (é preciso recriá-lo ou migrar para um plano pago para manter os dados).

## Estrutura

```
app/
  main.py       # rotas de links e página inicial
  auth.py       # rotas /auth e dependências de login
  security.py   # hash de senha (Argon2) e tokens JWT
  services.py   # regras de negócio (gerar código, clicar, apagar, usuários)
  models.py     # tabelas do banco (SQLAlchemy)
  schemas.py    # validação e formato das respostas (Pydantic)
  database.py   # conexão com o banco
  migrate.py    # aplica as migrações ao iniciar
  migrations/   # histórico do esquema do banco (Alembic)
  static/
    index.html  # interface web (HTML, CSS e JS puros, sem dependências)
tests/
  conftest.py        # fixtures (banco de teste, login)
  test_api.py        # links, redirecionamento e erros
  test_auth.py       # cadastro, login, tokens e dono dos links
  test_migrations.py # migrações x modelos
  test_database.py   # URL do banco
```

## Decisões de projeto

- **`secrets` em vez de `random`**: códigos não previsíveis.
- **`UPDATE clicks = clicks + 1` no banco**: evita perder cliques em acessos simultâneos.
- **307 em vez de 301**: o navegador não faz cache do redirecionamento, então os cliques continuam sendo contados.
- **Camada de serviço separada das rotas**: facilita testar e trocar o banco depois.
- **Argon2id para senhas e JWT com expiração**: a senha nunca é guardada em texto; o login leva o mesmo tempo com e-mail inexistente ou senha errada e devolve a mesma mensagem, para não revelar quais e-mails têm conta.
- **Token inválido nunca vira "anônimo"**: se a requisição traz um token ruim ou expirado, a API responde 401 em vez de criar o link sem dono.
- **Link de outra pessoa responde 404 (não 403)**: não revela quais códigos existem. Links anônimos (criados sem login) não podem ser listados nem apagados pela API.
- **Limitação conhecida**: na interface web o token fica no `localStorage`, que um XSS conseguiria ler. Por isso todo texto vindo da API entra na página com `textContent`. Cookies `HttpOnly` com proteção CSRF seriam a evolução natural.
- **Migrações no início da API**: simples para uma instância única. Com várias instâncias subindo ao mesmo tempo, o ideal é rodar `alembic upgrade head` como um passo separado do deploy.

## Próximos passos

- [ ] Expiração de links
- [x] Front-end simples (página única em `/`)
- [x] Autenticação (JWT) e links por usuário
- [x] Dockerfile
- [x] GitHub Actions rodando os testes
- [x] Configuração de deploy (Render)
- [x] Link da demo online neste README
- [x] Trocar SQLite por PostgreSQL (persistência)
- [x] Rodar os testes também contra PostgreSQL no CI
- [x] Migrações de banco com Alembic
- [ ] Limite de tentativas de login (rate limiting)
- [ ] Cookies `HttpOnly` no lugar do `localStorage`
