# G-GÁS — Catálogo de API

Prefixos em `ggas/urls.py`. Envelope de negócio: `status`, `message`, `data`. Listas incluem `count`, `next` e `previous`. O token é a exceção e não usa envelope.

Autenticação das rotas privadas: `Authorization: Bearer <access>`.

## Sistema e sessão

| Método | Rota | Acesso |
| --- | --- | --- |
| GET | `/api/health/` | Público. Confere o SQLite |
| GET | `/api/schema/` | Schema OpenAPI |
| GET | `/api/schema/swagger/` | Swagger |
| GET | `/api/schema/redoc/` | Redoc |
| POST | `/auth/token_jwt/` | Público. Corpo `username` e `password`. `username` aceita e-mail |
| POST | `/auth/token_jwt/refresh/` | Público. Corpo `refresh` |
| POST | `/auth/token_jwt/verify/` | Público. Corpo `token` |
| GET | `/auth/eu/` | Autenticado |

## Colaboradores

| Método | Rota | Permissão |
| --- | --- | --- |
| POST | `/colaboradores/` | `gestao_colaboradores` |
| GET | `/colaboradores/listar/` | Autenticado. Filtros `perfil`, `ativo`, `nome__icontains`, `ordering`. A lista traz `total_pedidos` e `pedidos_entregues` |
| GET | `/colaboradores/<id>/` | Autenticado |
| PATCH | `/colaboradores/<id>/atualizar/` | `gestao_colaboradores` |
| POST | `/colaboradores/<id>/conta/` | `gestao_colaboradores` |
| PATCH | `/colaboradores/<id>/conta/atualizar/` | `gestao_colaboradores` |

## Clientes, catálogo e auditoria

| Método | Rota | Quem grava | Quem lê |
| --- | --- | --- | --- |
| POST | `/clientes/` | `cadastrar_cliente` | |
| GET | `/clientes/listar/` | | Autenticado. `q` em nome, telefone e endereço; também `cidade` e `ordering` (`nome`, `created_at`) |
| GET | `/clientes/<id>/` | | Autenticado |
| PATCH | `/clientes/<id>/atualizar/` | `cadastrar_cliente` | |
| POST | `/produtos/` | `gerir_produto` | |
| GET | `/produtos/listar/` | | Autenticado. `q` em nome, marca e código; também `categoria`, `ativo`, `marca` e `ordering` (`nome`, `codigo`, `preco_venda`) |
| GET | `/produtos/<id>/` | | Autenticado |
| PATCH | `/produtos/<id>/atualizar/` | `gerir_produto` | |
| POST | `/fornecedores/` | `gerir_fornecedor` | |
| GET | `/fornecedores/listar/` | | Autenticado. `q` em fantasia, razão social e CNPJ; também `ativo`, `cidade` e `ordering` (`nome_fantasia`, `created_at`) |
| GET | `/fornecedores/<id>/` | | Autenticado |
| PATCH | `/fornecedores/<id>/atualizar/` | `gerir_fornecedor` | |
| GET | `/auditoria/listar/` | | `auditoria_sistema`. Filtros `tipo_entidade`, `acao`, `entidade_id`, `usuario`, `q` e `ordering` (`created_at`, `acao`) |
| GET | `/auditoria/<id>/` | | `auditoria_sistema` |

## Estoque

| Método | Rota | Permissão |
| --- | --- | --- |
| GET | `/estoque/movimentacoes/` | Autenticado. Filtros `q`, `produto`, `tipo`, `tipo_saldo`, `pedido_id`, `fornecedor`, `cliente` e `ordering` (`created_at`) |
| POST | `/estoque/entradas/` | `entrada_estoque` |
| POST | `/estoque/saidas/` | `saida_manual_estoque` |
| POST | `/estoque/conferencias/` | `conferencia_inventario` |

Entrada: `produto_id`, `fornecedor_id`, `quantidade`, `custo_unitario`, `motivo`.

Saída: `produto_id`, `quantidade`, `tipo` (`SAIDA_MANUAL_PERDA`, `SAIDA_MANUAL_AVARIA`, `SAIDA_MANUAL_CONSUMO`, `SAIDA_MANUAL_EMPRESTIMO`), `motivo`, `cliente_id` no empréstimo.

Conferência: `produto_id`, `contagem`, `motivo`.

## Pedidos

| Método | Rota | Permissão |
| --- | --- | --- |
| POST | `/pedidos/` | `nova_venda` |
| GET | `/pedidos/listar/` | Autenticado. Filtros `status`, `cliente`, `entregador`, `q` (código, cliente, telefone, entregador ou bairro), `de`, `ate` e `ordering` (`created_at`, `codigo`, `total`) |
| GET | `/pedidos/<id>/` | Autenticado |
| PATCH | `/pedidos/<id>/status/` | Autenticado. A regra interna escolhe confirmar, reabrir ou cancelar |

Corpo da venda: `cliente_id`, `entregador_id`, `itens` (`produto_id`, `quantidade`, `vazios_recebidos`), `forma_pagamento`, `valor_recebido`, `tipo_desconto`, `valor_desconto`, `observacoes`.

Corpo do status: `status` e `observacao`.

`de` e `ate` são `AAAA-MM-DD`, inclusivos, pelo dia local de `created_at`.

## Relatórios

| Método | Rota | Permissão |
| --- | --- | --- |
| GET | `/relatorios/painel/` | Autenticado |
| GET | `/relatorios/periodo/` | `relatorios_financeiros` |

`periodo` aceita `de` e `ate` juntos, ou nenhum dos dois.

### Painel (`data`)

- `faturamento_total`, `ticket_medio`: texto com duas casas.
- `pedidos_em_andamento`, `pedidos_entregues`, `pedidos_entregues_hoje`, `estoque_gas`, `estoque_agua`: inteiros.
- `alerta_estoque_minimo`: `id`, `nome`, `saldo_cheio`, `estoque_minimo`.
- `fila_despacho`: os 20 pendentes mais antigos. `id`, `codigo`, `nome_cliente`, `logradouro`, `numero`, `bairro`, `nome_entregador`, `total`, `itens` (`quantidade`, `nome_produto`). O total da fila continua em `pedidos_em_andamento`.
- `posicao_deposito`: `id`, `nome`, `marca`, `categoria`, `unidade`, `saldo_cheio`, `saldo_seco`, `estoque_minimo`.

### Período (`data`)

- `de`, `ate`.
- `pedidos_no_periodo`, `volume_pedidos`, `cancelados`.
- `faturamento_bruto`, `descontos`, `faturamento_liquido`, `ticket_medio`.
- `por_forma_pagamento`: `forma`, `quantidade`, `total`, `percentual` com uma casa. Ordem: `PIX`, `DINHEIRO`, `DEBITO`, `CREDITO`.
- `entregadores`: `id`, `nome`, `placa_veiculo`, `ativo`, `entregues`, `pendentes`, `faturamento`.
- `produtos_mais_vendidos`: `produto_id`, `nome`, `marca`, `quantidade`, `faturamento`.

A lista paginada de pedidos do período permanece em `GET /pedidos/listar/`.

## Fora do catálogo

Não há rota de cupom, impressão, dashboard alternativo, kanban, troca de usuário do protótipo, nem escrita de saldo direto no produto além do saldo de abertura.
