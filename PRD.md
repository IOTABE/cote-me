# PRD — Sistema de Cotações Online (cote-me)

> Documento de Requisitos de Produto
> Versão: 1.0
> Stack: Python 3.14 · Django 5.x · SQLite (dev) · PostgreSQL (prod) · Nginx · Gunicorn

---

## 1. Visão Geral

Plataforma web que conecta **Clientes** (solicitantes de cotação) a **Fornecedores** (respondentes) de forma automatizada. O cliente informa uma lista de produtos com suas categorias; a plataforma identifica os fornecedores aptos e dispara um convite por e-mail para cada um. As respostas ficam disponíveis para o cliente, com destaque automático para o menor preço de cada item. Após o fechamento do prazo, o cliente pode disparar pedidos automaticamente para os fornecedores vencedores.

---

## 2. Objetivos de Negócio

- Reduzir o tempo gasto pelo cliente em procurar e contatar fornecedores individualmente.
- Padronizar o processo de cotação, garantindo comparação justa (mesmo prazo, mesmas condições).
- Dar visibilidade ao fornecedor sem que ele precise "ficar procurando clientes".
- Automatizar a etapa de "fechamento" e geração de pedidos.

---

## 3. Atores

| Ator | Tipo | Descrição |
|------|------|-----------|
| **Cliente** | Pessoa física ou jurídica | Solicita cotações. Auto-cadastra-se e confirma e-mail. |
| **Fornecedor** | Pessoa jurídica | Recebe convites para cotar produtos de suas categorias. Pode responder via link único no e-mail ou via dashboard autenticado. |
| **Admin (Plataforma)** | Backoffice | Cadastra/gerencia categorias, produtos pré-cadastrados (opcional), fornecedores e visualiza todas as cotações. |
| **Sistema (job automático)** | Robô | Fecha cotações no prazo, dispara e-mails, calcula vencedores. |

---

## 4. Personas

### 4.1 Cliente
- **Quem:** Comprador de pequena/média empresa, gestor de compras, autônomo.
- **Necessidade:** Obter preço de vários fornecedores sem ter que ligar/enviar e-mail um a um.
- **Sucesso:** Receber ao menos 3 cotações para o mesmo item em até 48h.

### 4.2 Fornecedor
- **Quem:** Representante comercial ou empresa fornecedora.
- **Necessidade:** Receber pedidos de cotação qualificados (clientes reais, produtos da sua categoria).
- **Sucesso:** Responder cotação em menos de 2 minutos via celular.

### 4.3 Admin
- **Quem:** Operador da plataforma.
- **Necessidade:** Manter categorias/fornecedores atualizados e ter visão geral do fluxo.

---

## 5. Requisitos Funcionais

### 5.1 Autenticação e Cadastro

#### 5.1.1 Cliente — Auto-cadastro com confirmação por e-mail
- `RF001` Cliente acessa `/cliente/cadastro`, preenche: nome, e-mail, telefone, senha.
- `RF002` Sistema envia e-mail com link de confirmação contendo token de uso único (validade 24h).
- `RF003` Cliente clica no link → conta ativada → redirecionado para login.
- `RF004` Após login, cliente é direcionado ao dashboard de cotações.

#### 5.1.2 Fornecedor — Cadastro via Admin
- `RF005` Fornecedor é cadastrado pelo admin em `/admin` (não há auto-cadastro público).
- `RF006` Após cadastro, sistema gera automaticamente uma senha temporária e envia por e-mail ao fornecedor.
- `RF007` Fornecedor acessa `/fornecedor/login` com e-mail + senha. Pode alterar senha no primeiro acesso.

### 5.2 Catálogo

#### 5.2.1 Categorias
- `RF008` Admin gerencia categorias em `/admin` (nome, descrição, slug).
- `RF009` Categorias são exibidas como select-grouped no formulário de nova cotação.

#### 5.2.2 Produtos
- `RF010` Cliente informa produtos livremente no momento da cotação (nome, quantidade, unidade, categoria).
- `RF011` (Opcional) Admin pode pré-cadastrar produtos para sugestões. Quando o cliente digitar, sistema sugere.

#### 5.2.3 Fornecedor × Categoria
- `RF012` No cadastro do fornecedor, admin associa uma ou mais categorias a ele.
- `RF013` Apenas fornecedores com a categoria do item recebem convite para aquele item.

### 5.3 Cotação

#### 5.3.1 Criação
- `RF014` Cliente autenticado acessa `/cliente/cotacoes/nova`.
- `RF015` Adiciona um ou mais itens (nome, quantidade, unidade, categoria, descrição opcional).
- `RF016` Define prazo limite para respostas (padrão: 48h; mínimo: 1h; máximo: 30 dias).
- `RF017` Submete → status `ABERTA` → sistema dispara e-mails (ver 5.5).

#### 5.3.2 Recebimento pelo Fornecedor
- `RF018` Fornecedor recebe e-mail com: nome do cliente (sem documentos), lista de itens da sua categoria, prazo.
- `RF019` E-mail contém **link único assinado** (token + hash) com validade até o prazo.
- `RF020` Clicando no link, fornecedor acessa página para informar: preço unitário, prazo de entrega (dias), observações, marca opcional.
- `RF021` Se fornecedor já tiver login, pode também acessar `/fornecedor/cotacoes` no dashboard e responder de lá.

#### 5.3.3 Status da Cotação
| Status | Significado |
|--------|-------------|
| `ABERTA` | Criada, aguardando respostas. E-mails enviados. |
| `PARCIAL` | Algum fornecedor respondeu; ainda dentro do prazo. |
| `FECHADA` | Prazo expirado (rotina automática). Comparação liberada ao cliente. |
| `CANCELADA` | Cliente cancelou antes do prazo. |
| `PEDIDO_DISPARADO` | Cliente confirmou pedido para os itens vencedores. |

### 5.4 Visualização pelo Cliente

#### 5.4.1 Lista de cotações
- `RF022` Dashboard do cliente lista cotações com filtros (status, data, categoria).
- `RF023` Cada cotação mostra: nº itens, respostas recebidas / esperadas, prazo, status.

#### 5.4.2 Detalhe e comparação
- `RF024` Ao abrir cotação `FECHADA`, sistema agrupa respostas por item.
- `RF025` Para cada item, destaca visualmente o **menor preço** (cor verde, etiqueta "Melhor preço").
- `RF026` Mostra: preço unitário, preço total (qtd × preço), prazo de entrega, fornecedor, observações.
- `RF027` Enquanto `ABERTA` ou `PARCIAL`, cliente vê suas próprias cotações mas sem destaque de vencedor (apenas "X/Y responderam").

#### 5.4.3 Notificação por e-mail
- `RF028` Cliente recebe e-mail a cada nova resposta de fornecedor (com link para a cotação).
- `RF029` Cliente recebe e-mail quando a cotação é fechada automaticamente.

### 5.5 Envio de Pedidos

- `RF030` Após status `FECHADA`, em cada item o cliente vê botões: "Aceitar" / "Recusar" por fornecedor.
- `RF031` O sistema pré-seleciona o menor preço de cada item, mas cliente pode escolher outro fornecedor vencedor.
- `RF032` Cliente confirma → sistema cria um `Pedido` agrupado por fornecedor (todos os itens que ele venceu ficam no mesmo pedido).
- `RF033` Sistema envia e-mail ao fornecedor vencedor com o pedido (itens, quantidades, valores, dados do cliente).
- `RF034` Cotação muda para status `PEDIDO_DISPARADO` quando todos os itens têm vencedor definido.
- `RF035` Fornecedor vê seus pedidos em `/fornecedor/pedidos`.

### 5.6 Rotinas Automáticas (Jobs)

| Job | Frequência | Função |
|-----|-----------|--------|
| `fechar_cotacoes_expiradas` | A cada 5 min | Marca cotações com prazo vencido como `FECHADA` e dispara e-mail ao cliente. |
| `enviar_lembrete_fornecedor` | 1× por dia | Envia lembrete a fornecedores que ainda não responderam (a partir de 50% do prazo). |
| `limpar_tokens_expirados` | Diária | Remove tokens de confirmação e tokens de link único vencidos. |

> Em produção, usar `celery-beat` + `celery` com broker Redis. Em dev, usar `django-extensions` `jobs` ou `cron` do SO.

---

## 6. Requisitos Não-Funcionais

### 6.1 Segurança
- `RNF001` Senhas armazenadas com hash `argon2` (default Django 5).
- `RNF002` Tokens de link único: `secrets.token_urlsafe(32)` + `HMAC` (proteção contra enumeração).
- `RNF003` Fornecedor só vê/edita suas próprias respostas (regra no View + QuerySet).
- `RNF004` Cliente só vê suas próprias cotações.
- `RNF005` CSRF protection em todos os formulários; `Secure`, `HttpOnly`, `SameSite=Lax` em cookies.
- `RNF006` Em produção: `DEBUG=False`, `ALLOWED_HOSTS` restrito, `SECRET_KEY` em env var.

### 6.2 Desempenho
- `RNF007` Páginas do dashboard < 500ms para até 10k cotações.
- `RNF008` Envio de e-mail em fila (Celery) — não bloqueia a request do cliente.

### 6.3 Disponibilidade
- `RNF009` SLA alvo: 99% em horário comercial.
- `RNF010` Backup diário do PostgreSQL (responsabilidade operacional do deploy).

### 6.4 Usabilidade
- `RNF011` Mobile-first: a tela de resposta do fornecedor deve ser usável em celular (e-mail → link → formulário).
- `RNF012` Suporte a português (pt-BR).
- `RNF013` Acessibilidade básica: labels em inputs, contraste mínimo, foco visível.

### 6.5 Compatibilidade
- `RNF014` Navegadores: Chrome, Firefox, Safari (últimas 2 versões).
- `RNF015` Python 3.12+ (dev: 3.14 conforme `pyproject.toml`).

---

## 7. Modelo de Dados (resumo)

```
User (Django) ──┬── Cliente (FK 1-1)
                └── Fornecedor (FK 1-1) ── many-to-many ── Categoria

Categoria (id, nome, slug)

Cotacao (id, cliente_fk, prazo_limite, status, criada_em, fechada_em)
   └── ItemCotacao (id, cotacao_fk, produto_nome, qtd, unidade, categoria_fk, descricao)
          └── RespostaFornecedor (id, item_fk, fornecedor_fk, preco_unitario, prazo_dias, observacoes, created_at, UNIQUE(item, fornecedor))

Pedido (id, cotacao_fk, fornecedor_fk, status, total, created_at)
   └── ItemPedido (id, pedido_fk, item_cotacao_fk, qtd, preco_unitario)

EmailToken (id, user_fk, tipo, token_hash, expira_em, usado_em)   # confirmação, magic-link
```

---

## 8. Fluxos Principais (alto nível)

### 8.1 Cliente cria cotação
1. Login → `/cliente/cotacoes/nova` → adiciona itens → define prazo → submit.
2. Sistema agrupa itens por categoria.
3. Para cada categoria, busca fornecedores ativos daquela categoria.
4. Gera `RespostaFornecedor` (vazio) + token de link único por fornecedor.
5. Dispara e-mail para cada fornecedor.
6. Redireciona cliente para detalhe da cotação.

### 8.2 Fornecedor responde (via link)
1. Recebe e-mail → clica no link.
2. Sistema valida token (HMAC + não expirado + não usado).
3. Renderiza formulário com itens da cotação que pertencem à sua categoria.
4. Submete → resposta salva → marca token como usado → dispara e-mail ao cliente.

### 8.3 Fechamento automático
1. Job verifica cotações `ABERTA`/`PARCIAL` com `prazo_limite < now()`.
2. Marca como `FECHADA`.
3. Envia e-mail ao cliente com link para ver comparações.

### 8.4 Cliente dispara pedidos
1. Abre cotação `FECHADA`.
2. Para cada item, sistema mostra todas as respostas e pré-seleciona o menor preço.
3. Cliente confirma vencedores (pode ajustar) → submit.
4. Sistema agrupa por fornecedor → cria `Pedido` + `ItemPedido`.
5. Envia e-mail a cada fornecedor vencedor com o pedido.
6. Cotação → status `PEDIDO_DISPARADO`.

---

## 9. Stack Técnica

| Camada | Tecnologia |
|--------|-----------|
| Linguagem | Python 3.14 (dev) / 3.12+ (prod) |
| Framework | Django 5.x |
| Banco de dados | SQLite (dev) / PostgreSQL 16 (prod) |
| WSGI | Gunicorn 22+ |
| Reverse proxy | Nginx 1.24+ |
| Fila async | Celery + Redis (prod) |
| E-mail | SMTP configurável (Mailgun/SES/Sendgrid/Postfix) |
| Gerenciador de deps | uv |
| Estilo | Django Templates + CSS enxuto (sem framework JS no MVP) |

---

## 10. Configuração por Ambiente

### 10.1 Desenvolvimento
- `DJANGO_SETTINGS_MODULE=cote_me.settings.dev`
- Banco: SQLite em `db.sqlite3`
- E-mail: console backend
- `DEBUG=True`

### 10.2 Produção
- `DJANGO_SETTINGS_MODULE=cote_me.settings.prod`
- Banco: PostgreSQL (via `DATABASE_URL` ou vars individuais)
- E-mail: SMTP real
- `DEBUG=False`
- Servido por Gunicorn (unix socket) atrás de Nginx
- Variáveis sensíveis em `.env` (lido por `python-decouple` ou `django-environ`)

---

## 11. Entregáveis do MVP (Fase 1)

1. Modelos + migrations.
2. Cadastro/login de cliente.
3. Cadastro de fornecedor pelo admin + geração de senha.
4. CRUD de cotação pelo cliente.
5. Página de resposta do fornecedor (link + dashboard).
6. Sistema de e-mails (confirmação, convite, lembrete, notificação, pedido).
7. Job de fechamento automático.
8. Tela de comparação com destaque de vencedor.
9. Fluxo de geração de pedido.
10. Configurações Nginx + Gunicorn + systemd.
11. README de deploy.

---

## 12. Fora de Escopo (Fase 1)

- App mobile nativo.
- Pagamento integrado.
- Chat entre cliente e fornecedor.
- Avaliação de fornecedores.
- Multi-idioma (apenas pt-BR).
- Importação de produtos via planilha.
- API REST pública (apenas templates server-side no MVP).
