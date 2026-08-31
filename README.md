# Cote-me — Sistema de Cotações Online

Plataforma web que conecta **clientes** (solicitantes de cotação) a **fornecedores** (respondentes) de forma automatizada. O cliente informa uma lista de produtos; a plataforma identifica os fornecedores aptos e dispara convites por e-mail com link único (magic link). As respostas ficam disponíveis para o cliente, com destaque automático para o menor preço de cada item. Após o fechamento do prazo, o cliente pode disparar pedidos automaticamente para os fornecedores vencedores.

---

## Stack

| Camada | Tecnologia |
|--------|-----------|
| Linguagem | Python 3.12+ |
| Framework | Django 5.x |
| Banco de dados | SQLite (dev) / PostgreSQL 16 (prod) |
| WSGI | Gunicorn |
| Reverse proxy | Nginx |
| Fila assíncrona | Celery + Redis |
| Arquivos estáticos | WhiteNoise |
| Hash de senha | Argon2 |
| Gerenciador de deps | uv |
| Front-end | Django Templates + CSS glassmorphism (vanilla JS) |

---

## Estrutura do projeto

```
cote-me/
├── pyproject.toml
├── PRD.md
├── README.md
└── src/
    ├── manage.py
    ├── accounts/        # Modelo User custom, perfis Cliente/Fornecedor, auth
    ├── core/            # Landing page, tokens HMAC, tasks Celery, management commands
    ├── cotacoes/        # Cotações, itens, respostas, pedidos, comparação
    ├── cote_me/         # Configuração Django (settings split, urls, wsgi, celery)
    ├── static/          # CSS (glassmorphism.css), JS (app.js)
    └── templates/       # Templates base e parciais
```

### Apps Django

- **accounts** — Usuário customizado (`AbstractUser` com e-mail como login), perfis `Cliente` e `Fornecedor`, cadastro, login, confirmação por e-mail e primeiro acesso. 6 templates.
- **core** — Modelo `Categoria`, modelo `EmailToken` (confirmação de e-mail e magic-links), sistema de tokens assinados (HMAC-SHA256), tasks Celery (fechamento automático, lembretes) e management commands (`fechar_cotacoes`, `enviar_lembretes`).
- **cotacoes** — 6 modelos: `Cotacao`, `ItemCotacao`, `RespostaFornecedor`, `CotacaoTokenFornecedor`, `Pedido`, `ItemPedido`. Views separadas para cliente (5 views) e fornecedor (4 views), formsets dinâmicos, 3 templates de e-mail e 12 templates de página.

### Interface

- Tema **glassmorphism dark** com efeitos de vidro (`backdrop-filter: blur()`) e orbs de cor ambientes
- Google Fonts: **Inter** (texto) + **Material Symbols Rounded** (ícones)
- Design responsivo com breakpoint em 760px, sem framework JS (vanilla JS)
- Formsets inline dinâmicos com adicionar/remover linhas via JS

---

## Funcionalidades

### Cliente
- Auto-cadastro com confirmação por e-mail (token assinado HMAC)
- Dashboard com lista de cotações, filtros por status e barras de progresso
- Criação de cotação com múltiplos itens via formset dinâmico (JS)
- Comparação de preços com destaque "Melhor preço" por item
- Ranking de fornecedores por valor total
- Escolha de vencedores (manual ou pré-seleção automática do menor preço)
- Geração automática de pedidos agrupados por fornecedor
- Reenvio de cotação para fornecedores que não responderam

### Fornecedor
- Cadastro público com seleção de categorias e aprovação pelo admin
- Login dedicado (`/conta/fornecedor/login/`)
- Primeiro acesso com alteração obrigatória de senha
- Dashboard com cotações pendentes, respondidas e pedidos recebidos
- Resposta via magic link no e-mail (sem necessidade de login)
- Resposta autenticada pelo dashboard
- Visualização de pedidos recebidos

### Admin (Django Admin)
- Gestão de categorias (nome, slug, descrição, ativa)
- Aprovação/reprovação de fornecedores (ações em lote)
- Associação de categorias a fornecedores (filter horizontal)
- Visualização completa de cotações, respostas, tokens e pedidos
- Inlines para itens, respostas e itens de pedido

### Rotinas automáticas
- **Fechamento automático** de cotações expiradas (Celery task + management command)
- **Lembrete diário** a fornecedores que ainda não responderam (após 50% do prazo)
- Notificação por e-mail ao cliente quando fornecedor responde

---

## URLs

| Prefixo | Namespace | Descrição |
|---------|-----------|-----------|
| `/` | `core` | Landing page |
| `/conta/` | `accounts` | Login, cadastro, confirmação de e-mail |
| `/cliente/` | `cliente` | Dashboard, cotações, pedidos do cliente |
| `/fornecedor/` | `fornecedor` | Dashboard, respostas, pedidos do fornecedor |
| `/admin/` | — | Django Admin |

---

## Desenvolvimento

### Pré-requisitos

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)

### Instalação

```bash
# Clone o repositório
git clone <repo-url>
cd cote-me

# Instale as dependências
uv sync

# Rode as migrations
uv run python src/manage.py migrate

# Crie um superusuário (admin)
uv run python src/manage.py createsuperuser

# Inicie o servidor
uv run python src/manage.py runserver
```

O servidor estará disponível em `http://localhost:8000`.

### Variáveis de ambiente (dev)

Crie um arquivo `.env` na raiz do projeto (ao lado de `pyproject.toml`):

```env
DJANGO_SETTINGS_MODULE=cote_me.settings.dev
DJANGO_SECRET_KEY=dev-secret-key-not-for-production
BASE_URL=http://localhost:8000
```

Em desenvolvimento:
- Banco: SQLite (`db.sqlite3`)
- E-mail: console backend (mensagens aparecem no terminal)
- Celery: modo eager (tarefas executam sincronamente, sem worker)
- `DEBUG=True`

### Settings

O projeto usa settings divididos:

| Arquivo | Uso |
|---|---|
| `cote_me/settings/base.py` | Configurações compartilhadas |
| `cote_me/settings/dev.py` | Desenvolvimento: SQLite, e-mail no console, Celery eager |
| `cote_me/settings/prod.py` | Produção: PostgreSQL, SMTP, HTTPS, segurança reforçada |

### Management commands

```bash
# Fechar cotações com prazo expirado (uso em dev/CI)
uv run python src/manage.py fechar_cotacoes

# Enviar lembretes a fornecedores pendentes
uv run python src/manage.py enviar_lembretes
```

### Testes

```bash
uv run python src/manage.py test
```

---

## Produção

### Variáveis de ambiente

| Variável | Descrição |
|----------|-----------|
| `SECRET_KEY` | Chave secreta Django (obrigatória) |
| `TOKEN_HMAC_KEY` | Chave para assinatura HMAC de tokens (obrigatória) |
| `DB_NAME` | Nome do banco PostgreSQL |
| `DB_USER` | Usuário do banco |
| `DB_PASSWORD` | Senha do banco |
| `DB_HOST` | Host do banco |
| `DB_PORT` | Porta do banco |
| `BASE_URL` | URL base da aplicação (ex: `https://cotacoes.exemplo.com`) |
| `EMAIL_HOST` | Servidor SMTP |
| `EMAIL_PORT` | Porta SMTP |
| `EMAIL_HOST_USER` | Usuário SMTP |
| `EMAIL_HOST_PASSWORD` | Senha SMTP |
| `ALLOWED_HOSTS` | Domínios permitidos (separados por vírgula) |

### Deploy

```bash
uv run python src/manage.py migrate
uv run python src/manage.py collectstatic --noinput
gunicorn cote_me.wsgi:application --bind unix:/run/gunicorn/cote-me.sock
```

Configurações de segurança habilitadas em produção:
- SSL redirect + HSTS (30 dias, preload)
- Cookies seguros (`Secure`, `HttpOnly`, `SameSite=Lax`)
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`

---

## Fluxo principal

```
Cliente cria cotação com itens
        │
        ▼
Sistema agrupa itens por categoria
        │
        ▼
Fornecedores ativos da categoria recebem e-mail com magic link
        │
        ▼
Fornecedor responde (preço, prazo, marca, observações)
        │
        ▼
Prazo expira → cotação fecha automaticamente (Celery)
        │
        ▼
Cliente compara respostas (menor preço destacado)
        │
        ▼
Cliente escolhe vencedores → pedidos gerados automaticamente
        │
        ▼
Fornecedor vencedor recebe e-mail com o pedido
```

---

## Modelo de dados

```
User (custom, email como login) ──┬── Cliente (perfil 1:1)
                                  └── Fornecedor (perfil 1:1) ── M2M ── Categoria

Categoria (nome, slug, descrição, ativa)

Cotacao (cliente, prazo_limite, status, observacoes)
   ├── ItemCotacao (produto, quantidade, unidade, categoria, ordem)
   │      └── RespostaFornecedor (fornecedor, preço, prazo, marca, obs)
   └── CotacaoTokenFornecedor (magic link por fornecedor)

Pedido (cotacao, fornecedor, status, total)
   └── ItemPedido (item_cotacao, resposta_vencedora, quantidade, preço)

EmailToken (user, tipo, token_hash, expira_em)
```

**Status da cotação:** `aberta` → `parcial` → `fechada` → `pedido_disparado` (ou `cancelada`)

**Status do pedido:** `enviado` → `confirmado` → `em_producao` → `entregue` (ou `cancelado`)

---

## Segurança

- Senhas com hash **Argon2**
- Tokens de e-mail e magic links assinados com **HMAC-SHA256** (proteção contra enumeração)
- CSRF protection em todos os formulários
- Fornecedor só vê/edita suas próprias respostas (filtragem no QuerySet)
- Cliente só vê suas próprias cotações
- Validação de perfil por tipo de usuário (cliente/fornecedor)

---

## Licença

Privado — uso interno.
