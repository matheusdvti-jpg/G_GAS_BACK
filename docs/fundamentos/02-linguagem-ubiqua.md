# G-GÁS — Linguagem ubíqua

Use estes termos no código, na API e na conversa. O nome no model segue a coluna da direita.

| Termo | No código | Significado |
| --- | --- | --- |
| Colaborador | `Colaborador` | Pessoa da distribuidora, com perfil |
| Conta | `User` | Login ligado a um colaborador. O campo de acesso é `username` |
| Cliente | `Cliente` | Quem compra e recebe em um endereço |
| Produto | `Produto` | Item vendável: gás, água ou acessório |
| Cheio | `saldo_cheio` | Botijão ou galão pronto para venda. É o estoque que a venda baixa |
| Seco / vazio | `saldo_seco` | Vasilhame recolhido na troca. Gás: botijão seco. Água: galão vazio |
| Fornecedor | `Fornecedor` | Quem entrega carga. A lista de produtos que atende é texto, não vínculo |
| Movimentação | `MovimentacaoEstoque` | Lançamento que explica a mudança de saldo |
| Conferência | tipo `AJUSTE_INVENTARIO` | Contagem do cheio. A quantidade gravada é a diferença |
| Pedido | `Pedido` | Venda com itens, pagamento, entregador e status |
| Código do pedido | `codigo` | `PED-` e seis dígitos, gerado por `SequenciaPedido` |
| Despacho | status `PENDENTE` | Pedido aguardando entrega |
| Troca | `vazios_recebidos` | Vasilhames que o cliente devolve na venda |
| Troco | `troco` | Só existe no dinheiro. Nas outras formas fica zero |
| Painel | `GET /relatorios/painel/` | Visão operacional, sem filtro de data |
| Período / fechamento | `GET /relatorios/periodo/` | Relatório financeiro entre duas datas |
| Auditoria | `RegistroAuditoria` | Quem fez a ação, em qual entidade |

## Status do pedido

Só existem três:

- `PENDENTE` — registrado, ainda não entregue;
- `ENTREGUE` — entrega confirmada;
- `CANCELADO` — desfeito, com motivo. Não volta a outro status.

Não use `NOVO`, `EM_SEPARACAO`, `PRONTO_ENTREGA` nem `SAIU_ENTREGA`.

## Categorias e pagamento

Categorias: `GAS`, `AGUA`, `ACESSORIO`.

Pagamento: `DINHEIRO`, `PIX`, `DEBITO`, `CREDITO`.

Desconto: `NONE`, `VALUE`, `PERCENT`. O valor gravado no pedido é o desconto em reais já aplicado, mesmo quando a origem foi percentual.

## Perfis

`ADMINISTRADOR`, `GERENTE`, `ATENDENTE`, `ESTOQUISTA`, `ENTREGADOR`.

O entregador da venda é o `Colaborador` de perfil entregador, não o `User`.
