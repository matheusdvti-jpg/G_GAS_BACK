# G-GÁS — Observabilidade

O recorte atual é o de uma API local. Não há APM, métrica exportada nem alerta.

## Saúde

`GET /api/health/` executa `SELECT 1` no SQLite e responde o envelope com `banco: sqlite`. Falha de banco cai no tratamento de erro da view.

Use essa rota para saber se o processo e o arquivo respondem. Ela não mede fila, disco nem tempo de relatório.

## Log

`handle_exceptions` registra exceção inesperada e `SystemErrorException` no logger do Django, e devolve 500 sem o detalhe interno. Erro de regra volta 400 ao cliente e não é tratado como falha de sistema.

O simple-history guarda revisão de model. A auditoria de negócio guarda a ação de cadastro, estoque manual e pedido. São trilhas diferentes: uma é técnica, a outra é operacional.

## O que olhar quando um número não fecha

- Pedido cancelado sai do faturamento e permanece em `total_gasto` do cliente.
- Ticket do painel fica zero enquanto não houver nenhum pedido `ENTREGUE`.
- `pedidos_entregues_hoje` olha o histórico de status, não a data de criação do pedido.
- Seco no cancelamento pode baixar menos do que o vazio da venda se o saldo seco já foi consumido.
- Produto inativo não entra no depósito do painel.

## Quando a operação crescer

Aí sim: log em arquivo ou stdout com rotação, tempo de `GET /relatorios/periodo/`, espaço do `db.sqlite3` e, no PostgreSQL, conexão e trava. Nada disso está ligado agora.
