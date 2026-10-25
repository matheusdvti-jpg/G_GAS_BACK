# G-GÁS — Arquitetura de dados

Banco: SQLite em `G_GAS_BACK/db.sqlite3`. Fuso: `America/Sao_Paulo`, com `USE_TZ`. Moeda: `Decimal` com duas casas.

## Base

`BasicModel` acrescenta `created_at`, `updated_at` e `HistoricalRecords`. O histórico exclui `password`. O manager `get` de `objects` converte ausência em `NotFoundException`. `QuerySet.get`, inclusive depois de `select_for_update()`, ainda lança `DoesNotExist`. Essa tradução fica nos helpers de pedido e de estoque, descrita em [10-appcore-framework.md](10-appcore-framework.md).

`SequenciaPedido`, `ItemPedido` e `HistoricoStatusPedido` não herdam `BasicModel`. Não precisam de histórico próprio.

## Vínculos

```
Colaborador 1──1 User
Cliente 1──* Pedido
Colaborador (entregador) 1──* Pedido
User 1──* Pedido (criado_por)
Pedido 1──* ItemPedido *──1 Produto
Pedido 1──* HistoricoStatusPedido
Produto 1──* MovimentacaoEstoque
Fornecedor 0..1──* MovimentacaoEstoque
Cliente 0..1──* MovimentacaoEstoque
User 1──* MovimentacaoEstoque
User 1──* RegistroAuditoria
```

`MovimentacaoEstoque.pedido_id` é inteiro, sem integridade referencial com `Pedido`.

`Fornecedor.produtos_fornecidos` é uma lista JSON de nomes.

## Integridade operacional

- Código do pedido é único. A sequência `nome='pedido'` incrementa dentro da transação da venda.
- A mudança de status relê o pedido dentro da transação. O `get_object` da view fica de fora e não serve para decidir o estorno.
- Produto e cliente da venda são lidos com `select_for_update` antes da baixa, produtos em ordem de id. No SQLite essa cláusula não trava a linha. Quem serializa a escrita é `transaction_mode=IMMEDIATE`: a segunda venda espera a primeira terminar e então lê o saldo já baixado. No PostgreSQL, o `select_for_update` passa a travar a linha.
- `PROTECT` impede apagar cliente, produto, fornecedor, entregador ou usuário que já participou de pedido, movimento ou auditoria.
- Item do pedido cai em cascata com o pedido. O fluxo normal não apaga pedido.
- Índice em status e código do pedido, telefone e nome do cliente, tipo da movimentação e `pedido_id`, tipo e id da auditoria.

## O que cada tabela guarda de cópia

Pedido copia nome, telefone e endereço do cliente, e o nome do entregador. Item copia nome, marca e preço. Movimento copia nomes de produto, fornecedor, cliente e usuário. Auditoria copia o nome de quem executou. A leitura histórica não depende do cadastro atual.

## Leituras

Relatórios não criam tabela. O painel e o período agregam `Pedido`, `ItemPedido`, `Produto`, `Colaborador` e `HistoricoStatusPedido`.

Filtro de data do pedido e do relatório usa `created_at__date` no fuso local.

## Troca futura de banco

O ORM não usa SQL exclusivo do SQLite nas regras. A troca para PostgreSQL é mudança de `DATABASES` e das dependências, com as migrations já existentes. Não há segundo settings de banco agora.
