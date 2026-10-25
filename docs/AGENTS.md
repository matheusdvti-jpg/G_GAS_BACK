---
description: Diretrizes para agentes que alteram o back-end G-GÁS
alwaysApply: true
---

# G-GÁS — Diretrizes para agentes de IA

Leia este arquivo antes de implementar, refatorar ou documentar o back-end. A documentação canônica está em `docs/`. Em conflito entre memória do agente e os arquivos, prevalece `docs/` e o código.

O comportamento de negócio segue o front montado em `G_GAS_FRONT` (views e casos de uso). Documentos antigos do front, inclusive um quadro com seis status de pedido, não valem. O ciclo real é `PENDENTE`, `ENTREGUE` e `CANCELADO`.

## Escopo e prioridades

1. Siga as regras de [fundamentos/05-modelo-de-dominio-e-regras.md](fundamentos/05-modelo-de-dominio-e-regras.md) antes de implementar.
2. Não crie endpoint fora de [desenvolvimento/12-catalogo-de-api.md](desenvolvimento/12-catalogo-de-api.md) sem o pedido explícito de produto. Ao criar, atualize o catálogo e este arquivo no mesmo trabalho.
3. Regra de saldo, troca de vazio, status de pedido e permissão de perfil vem antes de tela ou relatório novo.
4. Ação crítica deixa rastro em auditoria: cadastro, conta, entrada e saída manual de estoque, conferência, criação de pedido e mudança de status. Venda e estorno de estoque não geram auditoria própria; o registro do pedido cobre os dois.
5. Responda ao usuário em português.

## O que consultar

| Tarefa | Documento |
| --- | --- |
| Visão e fluxos | [fundamentos/01-visao-geral-do-sistema.md](fundamentos/01-visao-geral-do-sistema.md) |
| Vocabulário | [fundamentos/02-linguagem-ubiqua.md](fundamentos/02-linguagem-ubiqua.md) |
| Fronteira entre apps | [fundamentos/03-bounded-contexts.md](fundamentos/03-bounded-contexts.md) |
| Regras de negócio | [fundamentos/05-modelo-de-dominio-e-regras.md](fundamentos/05-modelo-de-dominio-e-regras.md) |
| Stack e camadas | [arquitetura/04-arquitetura-da-solucao.md](arquitetura/04-arquitetura-da-solucao.md) |
| Models e concorrência | [arquitetura/06-arquitetura-de-dados.md](arquitetura/06-arquitetura-de-dados.md) |
| Views, envelope, permissão | [arquitetura/10-appcore-framework.md](arquitetura/10-appcore-framework.md) |
| Rotas | [desenvolvimento/12-catalogo-de-api.md](desenvolvimento/12-catalogo-de-api.md) |
| Testes | [desenvolvimento/11-testes.md](desenvolvimento/11-testes.md) |
| Setup | [desenvolvimento/00-setup-local.md](desenvolvimento/00-setup-local.md) |
| Ligar o painel | [desenvolvimento/13-integracao-front.md](desenvolvimento/13-integracao-front.md) |
| Ambiente | [operacao/07-deploy-e-operacao.md](operacao/07-deploy-e-operacao.md) |

## Restrições de implementação

### AppCore e camadas

- Domínio com regra usa `business.py`, `rules.py` e `helpers.py`.
- A view recebe HTTP e delega. O `business` orquestra. O `rules` aceita ou lança erro. O serializer não concentra regra de negócio.
- Use `AllowAnyMixin`, `AutenticadoMixin` ou `PermissaoMixin`. A permissão da rota é o atributo `permissao`. Não declare `permission_classes` na view. A troca de status do pedido fica autenticada: o `rules` escolhe `confirmar_entrega`, `reabrir_pedido` ou `cancelar_venda`.
- Listagem expõe filtro em `filterset_fields` ou `FilterSet` e documenta os parâmetros com `@extend_schema` e `OpenApiParameter`.
- Não crie função solta no topo de `business.py` ou `helpers.py`. Use método da classe.
- Não abra `transaction.atomic()` no business quando a entrada é `BasicPostAPIView`, `BasicUpdateAPIView` ou `BasicDeleteAPIView`. Essas views já transacionam `do_action_*`. Leitura não precisa de transação.
- Não decida status, saldo ou último administrador com o objeto carregado no `get_object`. Esse carregamento ocorre antes do `atomic`. Releia dentro do `do_action`.
- Consulta (`select_related`, trava, sequência do pedido, busca de login) fica no `helpers`. A view só devolve o queryset.
- O serializer não interpreta data nem decide regra. `de` e `ate` seguem como texto até `LeituraRules`.
- `gestao_cadastros` não protege rota. Use `cadastrar_cliente`, `gerir_produto` ou `gerir_fornecedor`.

### Domínio que não se negocia no código

- Saldo cheio e saldo seco só mudam por movimentação depois do cadastro. O `POST` de produto pode gravar o saldo de abertura. O `PATCH` que altera `saldo_cheio` ou `saldo_seco` é recusado.
- Gás força o vazio igual à quantidade. Água exige o galão vazio na mesma quantidade. Acessório não gera vazio.
- Pedido nasce `PENDENTE`. Cancelado não muda de status. Entregador confirma só a própria entrega.
- Cancelamento estorna o cheio e devolve o seco até o piso zero. `total_pedidos` e `total_gasto` do cliente não voltam atrás.
- Estoque guarda `pedido_id` como inteiro, sem chave estrangeira para `Pedido`. Pedidos chama o business de estoque. Estoque não importa Pedidos.
- Cliente, produto e fornecedor não se referenciam por chave. O fornecedor guarda nomes de produtos.
- Telefone de cliente e fornecedor tem 10 ou 11 dígitos. O do colaborador exige ao menos 8 caracteres. CPF e CNPJ têm dígitos verificadores. Senha não entra em auditoria nem no histórico do model.

### Código

- Aspas simples, f-strings, imports absolutos, nomes de domínio em português, mensagens de erro em português.
- Dinheiro em `Decimal`, quantizado em centavos, serializado como texto com duas casas.
- No PowerShell, não encadeie comandos com `&&`. Use `; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }`.
- O interpretador do projeto é `G_GAS_BACK\venv\Scripts\python.exe`.

## Comandos

Na pasta `G_GAS_BACK`:

```powershell
.\venv\Scripts\Activate.ps1
python manage.py migrate
python manage.py seed_inicial
python manage.py runserver
python manage.py test Colaboradores.colaboradores.tests Auditoria.auditoria.tests Pedidos.pedidos.tests Relatorios.relatorios.tests --verbosity 1
```

Detalhe em [desenvolvimento/00-setup-local.md](desenvolvimento/00-setup-local.md).

## API

- Schema: `GET /api/schema/`
- Swagger: `/api/schema/swagger/`
- Redoc: `/api/schema/redoc/`
- Saúde: `GET /api/health/`

JWT:

- `POST /auth/token_jwt/` — access, refresh e `usuario`. Aceita usuário ou e-mail no campo `username`.
- `POST /auth/token_jwt/refresh/`
- `POST /auth/token_jwt/verify/`
- `GET /auth/eu/` — envelope com a sessão.

O login JWT não usa o envelope `status` / `message` / `data`. O restante da API de negócio usa.

## O que não fazer sem alinhamento

- Introduzir status de pedido além de `PENDENTE`, `ENTREGUE` e `CANCELADO`.
- Alterar saldo por fora de `Estoque` ou estornar `total_gasto` no cancelamento.
- Criar chave estrangeira de `MovimentacaoEstoque` para `Pedido`.
- Ligar fornecedor a produto por chave.
- Adicionar Celery, Redis, Channels ou PostgreSQL sem pedido explícito. O banco atual é SQLite.
- Gravar senha, hash ou token em auditoria.
- Commitar, fazer push ou alterar git config sem o usuário pedir.
- Afrouxar paginação, `Decimal`, permissão, status ou saldo do produto para o painel consumir a API. O ajuste fica no cliente, como em [desenvolvimento/13-integracao-front.md](desenvolvimento/13-integracao-front.md).
